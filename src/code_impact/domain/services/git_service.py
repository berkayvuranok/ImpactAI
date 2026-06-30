"""Git service domain port."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import UUID


@dataclass(frozen=True, slots=True)
class GitCommitInfo:
    sha: str
    message: str
    author_email: str
    author_name: str
    committed_at: datetime
    parent_shas: list[str]
    is_merge: bool = False


@dataclass(frozen=True, slots=True)
class CloneResult:
    local_path: Path
    head_sha: str
    branch: str
    is_new_clone: bool


class IGitService(ABC):
    @abstractmethod
    async def clone_or_pull(
        self,
        repository_id: UUID,
        url: str,
        branch: str,
    ) -> CloneResult: ...

    @abstractmethod
    async def list_commits(
        self,
        repository_id: UUID,
        branch: str,
        limit: int = 500,
        since_sha: str | None = None,
    ) -> list[GitCommitInfo]: ...

    @abstractmethod
    async def get_diff(
        self,
        repository_id: UUID,
        base_sha: str,
        head_sha: str,
    ) -> str: ...

    @abstractmethod
    async def get_file_content(
        self,
        repository_id: UUID,
        commit_sha: str,
        file_path: str,
    ) -> str | None: ...

    @abstractmethod
    async def list_source_files(
        self,
        repository_id: UUID,
        commit_sha: str,
    ) -> list[str]: ...

    @abstractmethod
    def get_local_path(self, repository_id: UUID) -> Path: ...
