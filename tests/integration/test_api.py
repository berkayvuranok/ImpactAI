"""API integration tests with in-memory repositories."""

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from code_impact.application.use_cases import (
    AnalyzeDiffUseCase,
    CreateRepositoryUseCase,
    GetRepositoryUseCase,
    SyncRepositoryUseCase,
)
from code_impact.infrastructure.config.settings import Settings
from code_impact.presentation.api.app import create_app
from code_impact.presentation.api.dependencies import (
    get_analyze_diff_use_case,
    get_create_repository_use_case,
    get_get_repository_use_case,
    get_sync_repository_use_case,
    get_task_dispatcher,
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

    def dispatch_sync_repository(
        self,
        repository_id: str,
        job_id: str,
        full_sync: bool,
        since_sha: str | None,
    ) -> None:
        self.calls.append((repository_id, job_id, full_sync, since_sha))


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
    }


@pytest.fixture
def fake_dispatcher():
    return FakeTaskDispatcher()


@pytest.fixture
def app(test_settings: Settings, memory_repos, fake_dispatcher):
    application = create_app(test_settings, skip_bootstrap=True)

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
async def test_predict_accepted(client: AsyncClient):
    response = await client.post(
        "/api/v1/predict",
        json={
            "repository_id": str(uuid4()),
            "diff": "diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py",
        },
    )
    assert response.status_code == 202
