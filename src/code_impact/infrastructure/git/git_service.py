"""Git operations via GitPython — runs blocking I/O in thread pool."""

from __future__ import annotations

import asyncio
import re
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import git
from git import Repo

from code_impact.domain.exceptions import RepositorySyncError
from code_impact.domain.services.git_service import CloneResult, GitCommitInfo, IGitService
from code_impact.infrastructure.config.logging import get_logger
from code_impact.infrastructure.graph.source_files import is_source_file

logger = get_logger(__name__)

REVERT_PATTERN = re.compile(r"^revert(?:\s+\"(.+)\")?", re.IGNORECASE)


class GitService(IGitService):
    def __init__(self, storage_path: str, max_repo_size_mb: int = 500) -> None:
        self._storage_path = Path(storage_path)
        self._max_repo_size_mb = max_repo_size_mb
        self._storage_path.mkdir(parents=True, exist_ok=True)

    def get_local_path(self, repository_id: UUID) -> Path:
        return self._storage_path / str(repository_id)

    async def clone_or_pull(
        self,
        repository_id: UUID,
        url: str,
        branch: str,
    ) -> CloneResult:
        return await asyncio.to_thread(self._clone_or_pull_sync, repository_id, url, branch)

    async def list_commits(
        self,
        repository_id: UUID,
        branch: str,
        limit: int = 500,
        since_sha: str | None = None,
    ) -> list[GitCommitInfo]:
        return await asyncio.to_thread(
            self._list_commits_sync, repository_id, branch, limit, since_sha
        )

    async def get_diff(
        self,
        repository_id: UUID,
        base_sha: str,
        head_sha: str,
    ) -> str:
        return await asyncio.to_thread(self._get_diff_sync, repository_id, base_sha, head_sha)

    async def get_file_content(
        self,
        repository_id: UUID,
        commit_sha: str,
        file_path: str,
    ) -> str | None:
        return await asyncio.to_thread(
            self._get_file_content_sync, repository_id, commit_sha, file_path
        )

    async def list_source_files(
        self,
        repository_id: UUID,
        commit_sha: str,
    ) -> list[str]:
        return await asyncio.to_thread(
            self._list_source_files_sync, repository_id, commit_sha
        )

    def _open_repo(self, repository_id: UUID) -> Repo:
        repo_path = self.get_local_path(repository_id)
        if not repo_path.exists():
            msg = f"Repository not cloned: {repository_id}"
            raise RepositorySyncError(msg)
        return Repo(str(repo_path))

    def _clone_or_pull_sync(
        self,
        repository_id: UUID,
        url: str,
        branch: str,
    ) -> CloneResult:
        repo_path = self.get_local_path(repository_id)
        is_new_clone = False

        try:
            if repo_path.exists() and (repo_path / ".git").exists():
                repo = Repo(str(repo_path))
                origin = repo.remotes.origin
                origin.fetch(depth=1)
                repo.git.checkout(branch)
                origin.pull()
                head_sha = repo.head.commit.hexsha
                logger.info("git_pull_complete", repository_id=str(repository_id), head=head_sha)
            else:
                repo_path.mkdir(parents=True, exist_ok=True)
                repo = Repo.clone_from(url, str(repo_path), branch=branch, depth=500)
                is_new_clone = True
                head_sha = repo.head.commit.hexsha
                logger.info("git_clone_complete", repository_id=str(repository_id), head=head_sha)
        except git.GitCommandError as exc:
            msg = f"Git operation failed for {url}: {exc}"
            raise RepositorySyncError(msg) from exc

        return CloneResult(
            local_path=repo_path,
            head_sha=head_sha,
            branch=branch,
            is_new_clone=is_new_clone,
        )

    def _list_commits_sync(
        self,
        repository_id: UUID,
        branch: str,
        limit: int,
        since_sha: str | None,
    ) -> list[GitCommitInfo]:
        repo = self._open_repo(repository_id)
        kwargs: dict = {"max_count": limit}
        if since_sha:
            kwargs["rev"] = f"{since_sha}..{branch}"
        else:
            kwargs["rev"] = branch

        commits: list[GitCommitInfo] = []
        for commit in repo.iter_commits(**kwargs):
            commits.append(
                GitCommitInfo(
                    sha=commit.hexsha,
                    message=commit.message.strip(),
                    author_email=commit.author.email or "",
                    author_name=commit.author.name or "",
                    committed_at=datetime.fromtimestamp(commit.committed_date, tz=UTC),
                    parent_shas=[p.hexsha for p in commit.parents],
                    is_merge=len(commit.parents) > 1,
                )
            )
        return commits

    def _get_diff_sync(self, repository_id: UUID, base_sha: str, head_sha: str) -> str:
        repo = self._open_repo(repository_id)
        return repo.git.diff(base_sha, head_sha)

    def _get_file_content_sync(
        self, repository_id: UUID, commit_sha: str, file_path: str
    ) -> str | None:
        repo = self._open_repo(repository_id)
        try:
            blob = repo.commit(commit_sha).tree / file_path
            return blob.data_stream.read().decode("utf-8", errors="replace")
        except (KeyError, AttributeError, UnicodeDecodeError):
            return None

    def _list_source_files_sync(self, repository_id: UUID, commit_sha: str) -> list[str]:
        repo = self._open_repo(repository_id)
        commit = repo.commit(commit_sha)
        files: list[str] = []

        def walk(tree, prefix: str = "") -> None:
            for item in tree:
                path = f"{prefix}{item.name}" if not prefix else f"{prefix}/{item.name}"
                if item.type == "tree":
                    walk(item, path)
                elif item.type == "blob" and is_source_file(path):
                    files.append(path)

        walk(commit.tree)
        return sorted(files)


def is_rollback_commit(message: str) -> bool:
    return bool(REVERT_PATTERN.match(message.strip()))
