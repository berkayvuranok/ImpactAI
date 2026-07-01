"""FastAPI dependency injection."""

from collections.abc import AsyncGenerator
from uuid import UUID

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from code_impact.application.services.embedding_index_service import EmbeddingIndexService
from code_impact.application.services.graph_build_service import GraphBuildService
from code_impact.application.services.repository_sync_service import RepositorySyncService
from code_impact.application.use_cases import (
    AnalyzeDiffUseCase,
    CreateRepositoryUseCase,
    GetRepositoryUseCase,
    SyncRepositoryUseCase,
)
from code_impact.application.use_cases.embedding import IndexEmbeddingsUseCase, SearchSimilarUseCase
from code_impact.application.use_cases.graph import (
    BuildGraphUseCase,
    GetGraphUseCase,
    GetSubgraphUseCase,
)
from code_impact.domain.services import IEmbeddingService
from code_impact.domain.services.git_service import IGitService
from code_impact.domain.services.vector_store import IVectorStore
from code_impact.infrastructure.analysis.diff_analysis_service import DiffAnalysisService
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
    SqlAlchemyRepositoryRepository,
    SqlAlchemySyncJobRepository,
    SqlAlchemyUserRepository,
)
from code_impact.infrastructure.search.historical_search_service import HistoricalSearchService

# System user used until auth is implemented (Step 8+)
SYSTEM_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


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
