"""API integration tests with in-memory repositories."""

from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from code_impact.application.services.prediction_pipeline_service import PredictionPipelineService
from code_impact.application.use_cases import (
    AnalyzeDiffUseCase,
    CreateRepositoryUseCase,
    GetPredictionUseCase,
    GetRepositoryUseCase,
    PredictImpactUseCase,
    SyncRepositoryUseCase,
)
from code_impact.application.use_cases.prediction import RunPredictionPipelineUseCase
from code_impact.infrastructure.analysis.diff_analysis_service import DiffAnalysisService
from code_impact.infrastructure.config.settings import Settings
from code_impact.infrastructure.embeddings.mock_embedding_service import MockEmbeddingService
from code_impact.infrastructure.llm.template_explanation_generator import TemplateExplanationGenerator
from code_impact.infrastructure.recommendation.reviewer_recommender import ReviewerRecommender
from code_impact.infrastructure.search.historical_search_service import HistoricalSearchService
from code_impact.infrastructure.vector.in_memory_vector_store import InMemoryVectorStore
from code_impact.ml.inference.mock_gnn_predictor import MockGNNPredictor
from code_impact.presentation.api.app import create_app
from code_impact.presentation.api.dependencies import (
    get_analyze_diff_use_case,
    get_create_repository_use_case,
    get_get_prediction_use_case,
    get_get_repository_use_case,
    get_predict_impact_use_case,
    get_sync_repository_use_case,
    get_task_dispatcher,
)
from support.in_memory_graph_repository import InMemoryGraphRepository
from support.in_memory_prediction_repositories import (
    InMemoryPredictionRepository,
    InMemoryReviewerProfileRepository,
)
from support.in_memory_repositories import (
    InMemoryRepositoryRepository,
    InMemorySyncJobRepository,
)

SAMPLE_DIFF = """\
diff --git a/src/main.py b/src/main.py
--- a/src/main.py
+++ b/src/main.py
@@ -1,2 +1,5 @@
 def main():
     pass
+
+def cleanup():
+    pass
"""


class FakeTaskDispatcher:
    def __init__(self) -> None:
        self.calls: list[tuple] = []
        self.prediction_calls: list[str] = []
        self.pipeline: RunPredictionPipelineUseCase | None = None

    def dispatch_sync_repository(
        self,
        repository_id: str,
        job_id: str,
        full_sync: bool,
        since_sha: str | None,
    ) -> None:
        self.calls.append((repository_id, job_id, full_sync, since_sha))

    def dispatch_build_graph(self, repository_id: str, commit_sha: str) -> None:
        self.calls.append(("build_graph", repository_id, commit_sha))

    def dispatch_index_embeddings(
        self,
        repository_id: str,
        reindex: bool = False,
        include_issues: bool = True,
    ) -> None:
        self.calls.append(("index_embeddings", repository_id, reindex, include_issues))

    def dispatch_run_prediction(self, prediction_id: str) -> None:
        self.prediction_calls.append(prediction_id)


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        secret_key="test-secret-key-minimum-32-chars-long",
        database_url="postgresql+asyncpg://cip:cip_secret@localhost:5432/code_impact_test",
        redis_url="redis://localhost:6379/0",
        celery_broker_url="redis://localhost:6379/1",
        celery_result_backend="redis://localhost:6379/2",
        embedding_backend="mock",
        debug=True,
    )


@pytest.fixture
def memory_repos():
    return {
        "repository": InMemoryRepositoryRepository(),
        "sync_job": InMemorySyncJobRepository(),
        "prediction": InMemoryPredictionRepository(),
        "graph": InMemoryGraphRepository(),
        "reviewer": InMemoryReviewerProfileRepository(),
    }


@pytest.fixture
def fake_dispatcher():
    return FakeTaskDispatcher()


@pytest.fixture
def app(test_settings: Settings, memory_repos, fake_dispatcher):
    application = create_app(test_settings, skip_bootstrap=True)

    embeddings = MockEmbeddingService()
    search = HistoricalSearchService(InMemoryVectorStore(), embeddings, test_settings)
    pipeline_service = PredictionPipelineService(
        prediction_repo=memory_repos["prediction"],
        graph_repo=memory_repos["graph"],
        diff_service=DiffAnalysisService(),
        gnn_predictor=MockGNNPredictor(),
        historical_search=search,
        reviewer_recommender=ReviewerRecommender(memory_repos["reviewer"]),
        embedding_service=embeddings,
        explanation_generator=TemplateExplanationGenerator(),
    )
    fake_dispatcher.pipeline = RunPredictionPipelineUseCase(pipeline_service)

    application.dependency_overrides[get_create_repository_use_case] = (
        lambda: CreateRepositoryUseCase(memory_repos["repository"])
    )
    application.dependency_overrides[get_get_repository_use_case] = (
        lambda: GetRepositoryUseCase(memory_repos["repository"])
    )
    application.dependency_overrides[get_sync_repository_use_case] = (
        lambda: SyncRepositoryUseCase(memory_repos["repository"], memory_repos["sync_job"])
    )
    application.dependency_overrides[get_analyze_diff_use_case] = lambda: AnalyzeDiffUseCase()
    application.dependency_overrides[get_predict_impact_use_case] = lambda: PredictImpactUseCase(
        memory_repos["prediction"],
        memory_repos["repository"],
    )
    application.dependency_overrides[get_get_prediction_use_case] = lambda: GetPredictionUseCase(
        memory_repos["prediction"]
    )
    application.dependency_overrides[get_task_dispatcher] = lambda: fake_dispatcher

    return application


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_create_and_get_repository(client: AsyncClient):
    create_resp = await client.post(
        "/api/v1/repository",
        json={
            "name": "test-repo",
            "url": "https://github.com/example/test-repo",
            "default_branch": "main",
        },
    )
    assert create_resp.status_code == 201
    repo = create_resp.json()
    assert repo["name"] == "test-repo"

    get_resp = await client.get(f"/api/v1/repository/{repo['id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["url"] == "https://github.com/example/test-repo"


@pytest.mark.asyncio
async def test_get_repository_not_found(client: AsyncClient):
    response = await client.get(f"/api/v1/repository/{uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_sync_repository_queues_job(client: AsyncClient, fake_dispatcher: FakeTaskDispatcher):
    create_resp = await client.post(
        "/api/v1/repository",
        json={
            "name": "sync-repo",
            "url": "https://github.com/example/sync-repo",
        },
    )
    repo_id = create_resp.json()["id"]

    sync_resp = await client.post(
        f"/api/v1/repository/{repo_id}/sync",
        json={"full_sync": True},
    )
    assert sync_resp.status_code == 200
    data = sync_resp.json()
    assert data["status"] == "queued"
    assert len(fake_dispatcher.calls) == 1
    assert fake_dispatcher.calls[0][0] == repo_id


@pytest.mark.asyncio
async def test_analyze_diff(client: AsyncClient):
    response = await client.post(
        "/api/v1/analyze/diff",
        json={
            "diff": SAMPLE_DIFF,
            "file_contents_before": {"src/main.py": "def main():\n    pass\n"},
            "file_contents_after": {
                "src/main.py": "def main():\n    pass\n\ndef cleanup():\n    pass\n"
            },
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "src/main.py" in data["changed_files"]
    assert data["added_lines"] > 0
    assert any("cleanup" in fn for fc in data["file_changes"] for fn in fc["functions_added"])


@pytest.mark.asyncio
async def test_predict_and_get_result(client: AsyncClient, memory_repos, fake_dispatcher):
    create_resp = await client.post(
        "/api/v1/repository",
        json={
            "name": "predict-repo",
            "url": "https://github.com/example/predict-repo",
        },
    )
    repo_id = create_resp.json()["id"]

    predict_resp = await client.post(
        "/api/v1/predict",
        json={"repository_id": repo_id, "diff": SAMPLE_DIFF},
    )
    assert predict_resp.status_code == 202
    prediction_id = predict_resp.json()["prediction_id"]

    if fake_dispatcher.pipeline:
        await fake_dispatcher.pipeline.execute(UUID(prediction_id))

    get_resp = await client.get(f"/api/v1/prediction/{prediction_id}")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["status"] == "completed"
    assert data["risk_score"] is not None
    assert data["explanation"] is not None
    assert data["explanation"]["root_cause"]


@pytest.mark.asyncio
async def test_predict_unknown_repository_returns_404(client: AsyncClient):
    response = await client.post(
        "/api/v1/predict",
        json={
            "repository_id": str(uuid4()),
            "diff": "diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py",
        },
    )
    assert response.status_code == 404
