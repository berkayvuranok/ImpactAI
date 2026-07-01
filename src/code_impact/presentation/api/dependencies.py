"""FastAPI dependency injection."""

from collections.abc import AsyncGenerator
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from code_impact.application.services.embedding_index_service import EmbeddingIndexService
from code_impact.application.services.graph_build_service import GraphBuildService
from code_impact.application.services.prediction_pipeline_service import PredictionPipelineService
from code_impact.application.services.repository_sync_service import RepositorySyncService
from code_impact.application.services.webhook_handler_service import WebhookHandlerService
from code_impact.application.use_cases.auth import (
    LoginUseCase,
    RefreshTokenUseCase,
    RegisterUserUseCase,
)
from code_impact.application.use_cases.repository import DeleteRepositoryUseCase, ListRepositoriesUseCase
from code_impact.application.use_cases import (
    AnalyzeDiffUseCase,
    CreateRepositoryUseCase,
    GetPredictionUseCase,
    GetRepositoryUseCase,
    PredictImpactUseCase,
    SyncRepositoryUseCase,
)
from code_impact.application.use_cases.prediction import (
    GetPredictionHistoryUseCase,
    GetPredictionXAIUseCase,
    GetRiskSummaryUseCase,
    RunPredictionPipelineUseCase,
)
from code_impact.application.use_cases.embedding import IndexEmbeddingsUseCase, SearchSimilarUseCase
from code_impact.application.use_cases.graph import (
    BuildGraphUseCase,
    GetGraphUseCase,
    GetSubgraphUseCase,
)
from code_impact.domain.entities import User
from code_impact.domain.value_objects.enums import UserRole
from code_impact.domain.services.git_service import IGitService
from code_impact.domain.services.vector_store import IVectorStore
from code_impact.domain.services import IEmbeddingService
from code_impact.infrastructure.auth.jwt_service import JWTService
from code_impact.infrastructure.auth.rate_limiter import RateLimiter
from code_impact.domain.services import IGNNPredictor
from code_impact.infrastructure.config.settings import Settings
from code_impact.infrastructure.embeddings.mock_embedding_service import MockEmbeddingService
from code_impact.infrastructure.embeddings.sentence_transformer_service import (
    SentenceTransformerEmbeddingService,
)
from code_impact.infrastructure.git.git_service import GitService
from code_impact.infrastructure.graph.dependency_graph_builder import DependencyGraphBuilder
from code_impact.infrastructure.graph.graph_storage import GraphStorage
from code_impact.infrastructure.queue.task_dispatcher import CeleryTaskDispatcher, ITaskDispatcher
from code_impact.infrastructure.persistence.repositories import (
    SqlAlchemyCommitRepository,
    SqlAlchemyEmbeddingRepository,
    SqlAlchemyGraphRepository,
    SqlAlchemyIssueRepository,
    SqlAlchemyPredictionRepository,
    SqlAlchemyRepositoryRepository,
    SqlAlchemyReviewerProfileRepository,
    SqlAlchemySyncJobRepository,
    SqlAlchemyUserRepository,
)
from code_impact.infrastructure.recommendation.reviewer_recommender import ReviewerRecommender
from code_impact.infrastructure.search.historical_search_service import HistoricalSearchService
from code_impact.infrastructure.llm.factory import build_explanation_generator
from code_impact.ml.risk.ensemble_fusion import EnsembleFusionService
from code_impact.ml.xai import XAIService

# System user for bootstrap and auth-disabled mode
SYSTEM_USER_ID = UUID("00000000-0000-0000-0000-000000000001")
SYSTEM_USER_EMAIL = "system@code-impact.local"

_bearer = HTTPBearer(auto_error=False)


async def get_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    session_factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_git_service(settings: Settings = Depends(get_settings)) -> IGitService:
    return GitService(
        storage_path=settings.git_storage_path,
        max_repo_size_mb=settings.max_repo_size_mb,
    )


def get_create_repository_use_case(
    session: AsyncSession = Depends(get_session),
) -> CreateRepositoryUseCase:
    return CreateRepositoryUseCase(SqlAlchemyRepositoryRepository(session))


def get_get_repository_use_case(
    session: AsyncSession = Depends(get_session),
) -> GetRepositoryUseCase:
    return GetRepositoryUseCase(SqlAlchemyRepositoryRepository(session))


def get_sync_repository_use_case(
    session: AsyncSession = Depends(get_session),
) -> SyncRepositoryUseCase:
    return SyncRepositoryUseCase(
        SqlAlchemyRepositoryRepository(session),
        SqlAlchemySyncJobRepository(session),
    )


def get_repository_sync_service(
    session: AsyncSession = Depends(get_session),
    git_service: IGitService = Depends(get_git_service),
) -> RepositorySyncService:
    return RepositorySyncService(
        git_service=git_service,
        repository_repo=SqlAlchemyRepositoryRepository(session),
        commit_repo=SqlAlchemyCommitRepository(session),
        sync_job_repo=SqlAlchemySyncJobRepository(session),
    )


def get_analyze_diff_use_case() -> AnalyzeDiffUseCase:
    return AnalyzeDiffUseCase(DiffAnalysisService())


def get_user_repository(session: AsyncSession = Depends(get_session)) -> SqlAlchemyUserRepository:
    return SqlAlchemyUserRepository(session)


def get_task_dispatcher() -> ITaskDispatcher:
    return CeleryTaskDispatcher()


def get_graph_build_service(
    session: AsyncSession = Depends(get_session),
    git_service: IGitService = Depends(get_git_service),
    settings: Settings = Depends(get_settings),
) -> GraphBuildService:
    return GraphBuildService(
        graph_builder=DependencyGraphBuilder(git_service),
        graph_repo=SqlAlchemyGraphRepository(session),
        repository_repo=SqlAlchemyRepositoryRepository(session),
        graph_storage=GraphStorage(settings.graph_storage_path),
    )


def get_build_graph_use_case(
    graph_build_service: GraphBuildService = Depends(get_graph_build_service),
) -> BuildGraphUseCase:
    return BuildGraphUseCase(graph_build_service)


def get_get_graph_use_case(
    session: AsyncSession = Depends(get_session),
) -> GetGraphUseCase:
    return GetGraphUseCase(SqlAlchemyGraphRepository(session))


def get_get_subgraph_use_case(
    session: AsyncSession = Depends(get_session),
) -> GetSubgraphUseCase:
    return GetSubgraphUseCase(SqlAlchemyGraphRepository(session))


def get_embedding_service(settings: Settings = Depends(get_settings)) -> IEmbeddingService:
    if settings.embedding_backend == "mock":
        return MockEmbeddingService()
    return SentenceTransformerEmbeddingService(settings.embedding_model)


def get_vector_store(settings: Settings = Depends(get_settings)) -> IVectorStore:
    from code_impact.infrastructure.vector.qdrant_store import QdrantVectorStore

    return QdrantVectorStore(host=settings.qdrant_host, port=settings.qdrant_port)


def get_embedding_index_service(
    session: AsyncSession = Depends(get_session),
    git_service: IGitService = Depends(get_git_service),
    embedding_service: IEmbeddingService = Depends(get_embedding_service),
    vector_store: IVectorStore = Depends(get_vector_store),
    settings: Settings = Depends(get_settings),
) -> EmbeddingIndexService:
    return EmbeddingIndexService(
        embedding_service=embedding_service,
        vector_store=vector_store,
        embedding_repo=SqlAlchemyEmbeddingRepository(session),
        commit_repo=SqlAlchemyCommitRepository(session),
        issue_repo=SqlAlchemyIssueRepository(session),
        git_service=git_service,
        settings=settings,
    )


def get_historical_search_service(
    embedding_service: IEmbeddingService = Depends(get_embedding_service),
    vector_store: IVectorStore = Depends(get_vector_store),
    settings: Settings = Depends(get_settings),
) -> HistoricalSearchService:
    return HistoricalSearchService(vector_store, embedding_service, settings)


def get_index_embeddings_use_case(
    index_service: EmbeddingIndexService = Depends(get_embedding_index_service),
) -> IndexEmbeddingsUseCase:
    return IndexEmbeddingsUseCase(index_service)


def get_search_similar_use_case(
    search_service: HistoricalSearchService = Depends(get_historical_search_service),
) -> SearchSimilarUseCase:
    return SearchSimilarUseCase(search_service)


def get_gnn_predictor(settings: Settings = Depends(get_settings)) -> IGNNPredictor:
    from code_impact.ml.inference.gnn_predictor import GNNPredictor
    from code_impact.ml.inference.mock_gnn_predictor import MockGNNPredictor

    if settings.gnn_backend == "mock":
        return MockGNNPredictor()
    predictor = GNNPredictor(settings.gnn_model_path, device=settings.inference_device)
    if not predictor.is_loaded:
        return MockGNNPredictor()
    return predictor


def get_prediction_pipeline_service(
    session: AsyncSession = Depends(get_session),
    gnn_predictor: IGNNPredictor = Depends(get_gnn_predictor),
    historical_search: HistoricalSearchService = Depends(get_historical_search_service),
    embedding_service: IEmbeddingService = Depends(get_embedding_service),
    settings: Settings = Depends(get_settings),
) -> PredictionPipelineService:
    return PredictionPipelineService(
        prediction_repo=SqlAlchemyPredictionRepository(session),
        graph_repo=SqlAlchemyGraphRepository(session),
        diff_service=DiffAnalysisService(),
        gnn_predictor=gnn_predictor,
        historical_search=historical_search,
        reviewer_recommender=ReviewerRecommender(SqlAlchemyReviewerProfileRepository(session)),
        embedding_service=embedding_service,
        explanation_generator=build_explanation_generator(settings),
        xai_service=XAIService(use_shap_library=settings.xai_use_shap_library),
        xai_enabled=settings.xai_enabled,
        ensemble=EnsembleFusionService(
            gnn_weight=settings.ensemble_gnn_weight,
            classical_weight=settings.ensemble_classical_weight,
            historical_weight=settings.ensemble_historical_weight,
        ),
    )


def get_predict_impact_use_case(
    session: AsyncSession = Depends(get_session),
) -> PredictImpactUseCase:
    return PredictImpactUseCase(
        SqlAlchemyPredictionRepository(session),
        SqlAlchemyRepositoryRepository(session),
    )


def get_get_prediction_use_case(
    session: AsyncSession = Depends(get_session),
) -> GetPredictionUseCase:
    return GetPredictionUseCase(SqlAlchemyPredictionRepository(session))


def get_get_prediction_history_use_case(
    session: AsyncSession = Depends(get_session),
) -> GetPredictionHistoryUseCase:
    return GetPredictionHistoryUseCase(SqlAlchemyPredictionRepository(session))


def get_get_risk_summary_use_case(
    session: AsyncSession = Depends(get_session),
) -> GetRiskSummaryUseCase:
    return GetRiskSummaryUseCase(SqlAlchemyPredictionRepository(session))


def get_get_prediction_xai_use_case(
    session: AsyncSession = Depends(get_session),
) -> GetPredictionXAIUseCase:
    return GetPredictionXAIUseCase(SqlAlchemyPredictionRepository(session))


def get_run_prediction_pipeline_use_case(
    pipeline: PredictionPipelineService = Depends(get_prediction_pipeline_service),
) -> RunPredictionPipelineUseCase:
    return RunPredictionPipelineUseCase(pipeline)


def get_jwt_service(settings: Settings = Depends(get_settings)) -> JWTService:
    return JWTService(settings)


def get_rate_limiter(settings: Settings = Depends(get_settings)) -> RateLimiter:
    return RateLimiter(settings)


def get_register_user_use_case(
    session: AsyncSession = Depends(get_session),
    jwt_service: JWTService = Depends(get_jwt_service),
) -> RegisterUserUseCase:
    return RegisterUserUseCase(SqlAlchemyUserRepository(session), jwt_service)


def get_login_use_case(
    session: AsyncSession = Depends(get_session),
    jwt_service: JWTService = Depends(get_jwt_service),
) -> LoginUseCase:
    return LoginUseCase(SqlAlchemyUserRepository(session), jwt_service)


def get_refresh_token_use_case(
    session: AsyncSession = Depends(get_session),
    jwt_service: JWTService = Depends(get_jwt_service),
) -> RefreshTokenUseCase:
    return RefreshTokenUseCase(SqlAlchemyUserRepository(session), jwt_service)


def get_list_repositories_use_case(
    session: AsyncSession = Depends(get_session),
) -> ListRepositoriesUseCase:
    return ListRepositoriesUseCase(SqlAlchemyRepositoryRepository(session))


def get_delete_repository_use_case(
    session: AsyncSession = Depends(get_session),
) -> DeleteRepositoryUseCase:
    return DeleteRepositoryUseCase(SqlAlchemyRepositoryRepository(session))


def get_webhook_handler(
    session: AsyncSession = Depends(get_session),
    dispatcher: ITaskDispatcher = Depends(get_task_dispatcher),
) -> WebhookHandlerService:
    return WebhookHandlerService(
        repository_repo=SqlAlchemyRepositoryRepository(session),
        predict_use_case=PredictImpactUseCase(
            SqlAlchemyPredictionRepository(session),
            SqlAlchemyRepositoryRepository(session),
        ),
        task_dispatcher=dispatcher,
    )


async def get_current_user(
    settings: Settings = Depends(get_settings),
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    session: AsyncSession = Depends(get_session),
) -> User:
    if not settings.auth_enabled:
        user_repo = SqlAlchemyUserRepository(session)
        user = await user_repo.get_by_id(SYSTEM_USER_ID)
        if user:
            return user
        return User(
            id=SYSTEM_USER_ID,
            email=SYSTEM_USER_EMAIL,
            username="system",
            hashed_password="!",
            role=UserRole.ADMIN,
        )

    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    jwt_service = JWTService(settings)
    try:
        payload = jwt_service.decode_token(credentials.credentials, expected_type="access")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    user = await SqlAlchemyUserRepository(session).get_by_id(UUID(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
