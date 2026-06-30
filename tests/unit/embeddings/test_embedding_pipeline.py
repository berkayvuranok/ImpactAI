"""Integration tests for embedding index + historical search."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from code_impact.application.services.embedding_index_service import EmbeddingIndexService
from code_impact.application.use_cases.embedding import IndexEmbeddingsCommand, IndexEmbeddingsUseCase, SearchSimilarCommand, SearchSimilarUseCase
from code_impact.domain.entities import Commit, Issue
from code_impact.infrastructure.config.settings import Settings
from code_impact.infrastructure.embeddings.mock_embedding_service import MockEmbeddingService
from code_impact.infrastructure.search.historical_search_service import HistoricalSearchService
from code_impact.infrastructure.vector.in_memory_vector_store import InMemoryVectorStore
from support.in_memory_embedding_repositories import (
    InMemoryEmbeddingRepository,
    InMemoryIssueRepository,
)
from support.in_memory_repositories import InMemoryCommitRepository


class FakeGit:
    async def get_diff(self, repository_id, base_sha, head_sha):
        return "diff content changed api handler"


@pytest.fixture
def repo_id():
    return uuid4()


@pytest.fixture
def settings():
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
def commit_repo():
    return InMemoryCommitRepository()


@pytest.fixture
def embedding_repo():
    return InMemoryEmbeddingRepository()


@pytest.fixture
def issue_repo():
    return InMemoryIssueRepository()


@pytest.fixture
def vector_store():
    return InMemoryVectorStore()


@pytest.fixture
def embedding_service():
    return MockEmbeddingService()


@pytest.fixture
def index_service(commit_repo, embedding_repo, issue_repo, vector_store, embedding_service, settings):
    return EmbeddingIndexService(
        embedding_service=embedding_service,
        vector_store=vector_store,
        embedding_repo=embedding_repo,
        commit_repo=commit_repo,
        issue_repo=issue_repo,
        git_service=FakeGit(),
        settings=settings,
    )


@pytest.fixture
def search_service(vector_store, embedding_service, settings):
    return HistoricalSearchService(vector_store, embedding_service, settings)


@pytest.mark.asyncio
async def test_index_and_search_similar_commits(
    repo_id, commit_repo, issue_repo, index_service, search_service
):
    c1 = Commit(
        id=uuid4(),
        repository_id=repo_id,
        sha="abc111",
        message="Fix payment regression in checkout",
        author_email="dev@example.com",
        committed_at=datetime.now(UTC),
        is_regression=True,
        metadata={"parent_shas": ["parent1"]},
    )
    c2 = Commit(
        id=uuid4(),
        repository_id=repo_id,
        sha="def222",
        message="Update README documentation",
        author_email="dev@example.com",
        committed_at=datetime.now(UTC),
        metadata={"parent_shas": ["parent2"]},
    )
    await commit_repo.create_batch([c1, c2])

    await issue_repo.create_batch([
        Issue(
            id=uuid4(),
            repository_id=repo_id,
            external_id="BUG-42",
            title="Checkout payment failure",
            state="closed",
            issue_type="bug",
        )
    ])

    index_uc = IndexEmbeddingsUseCase(index_service)
    stats = await index_uc.execute(IndexEmbeddingsCommand(repository_id=repo_id))
    assert stats["commits"]["indexed"] == 2
    assert stats["issues"]["indexed"] == 1

    search_uc = SearchSimilarUseCase(search_service)
    result = await search_uc.execute(
        SearchSimilarCommand(
            repository_id=repo_id,
            diff="Fix payment regression in checkout handler",
            top_k_commits=2,
            top_k_bugs=1,
        )
    )

    assert len(result["similar_commits"]) >= 1
    assert result["similar_commits"][0]["commit_sha"] in ("abc111", "def222")
    assert len(result["similar_bugs"]) >= 1


@pytest.mark.asyncio
async def test_skip_already_indexed(repo_id, commit_repo, index_service, embedding_repo):
    commit = Commit(
        id=uuid4(),
        repository_id=repo_id,
        sha="sha1",
        message="Initial",
        author_email="a@b.com",
        committed_at=datetime.now(UTC),
    )
    await commit_repo.create_batch([commit])

    stats1 = await index_service.index_repository_commits(repo_id)
    assert stats1["indexed"] == 1

    stats2 = await index_service.index_repository_commits(repo_id)
    assert stats2["skipped"] == 1
    assert stats2["indexed"] == 0
