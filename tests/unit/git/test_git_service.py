"""Unit tests for GitService."""

import subprocess
from pathlib import Path
from uuid import uuid4

import pytest
from git import Repo

from code_impact.domain.exceptions import RepositorySyncError


def _default_branch(repo_path: Path) -> str:
    return Repo(str(repo_path)).active_branch.name


@pytest.fixture
def local_repo(tmp_path: Path) -> Path:
    repo_path = tmp_path / "sample-repo"
    repo_path.mkdir()
    subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    (repo_path / "main.py").write_text("def hello():\n    return 'world'\n")
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    (repo_path / "main.py").write_text("def hello():\n    return 'universe'\n")
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Update hello"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    return repo_path


@pytest.fixture
def git_service(tmp_path: Path):
    from code_impact.infrastructure.git.git_service import GitService

    return GitService(storage_path=str(tmp_path / "repos"))


class TestGitService:
    @pytest.mark.asyncio
    async def test_list_commits_from_existing_clone(
        self, git_service, local_repo: Path
    ):
        repo_id = uuid4()
        dest = git_service.get_local_path(repo_id)
        subprocess.run(
            ["git", "clone", str(local_repo), str(dest)],
            check=True,
            capture_output=True,
        )

        branch = _default_branch(dest)
        commits = await git_service.list_commits(repo_id, branch=branch, limit=10)
        assert len(commits) >= 2
        assert commits[0].sha != commits[1].sha

    @pytest.mark.asyncio
    async def test_get_diff(self, git_service, local_repo: Path):
        repo_id = uuid4()
        dest = git_service.get_local_path(repo_id)
        subprocess.run(
            ["git", "clone", str(local_repo), str(dest)],
            check=True,
            capture_output=True,
        )

        branch = _default_branch(dest)
        commits = await git_service.list_commits(repo_id, branch=branch, limit=10)
        diff = await git_service.get_diff(repo_id, commits[1].sha, commits[0].sha)
        assert "main.py" in diff

    @pytest.mark.asyncio
    async def test_get_file_content(self, git_service, local_repo: Path):
        repo_id = uuid4()
        dest = git_service.get_local_path(repo_id)
        subprocess.run(
            ["git", "clone", str(local_repo), str(dest)],
            check=True,
            capture_output=True,
        )

        branch = _default_branch(dest)
        commits = await git_service.list_commits(repo_id, branch=branch, limit=1)
        content = await git_service.get_file_content(repo_id, commits[0].sha, "main.py")
        assert content is not None
        assert "hello" in content

    @pytest.mark.asyncio
    async def test_uncloned_repo_raises(self, git_service):
        with pytest.raises(RepositorySyncError):
            await git_service.list_commits(uuid4(), branch="main")


class TestRollbackDetection:
    def test_revert_message(self):
        from code_impact.infrastructure.git.git_service import is_rollback_commit

        assert is_rollback_commit('Revert "Fix login bug"')
        assert is_rollback_commit("revert: broken feature")

    def test_normal_message(self):
        from code_impact.infrastructure.git.git_service import is_rollback_commit

        assert not is_rollback_commit("Fix login bug")
