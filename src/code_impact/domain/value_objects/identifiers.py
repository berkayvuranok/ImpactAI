"""Strongly-typed domain identifiers."""

from typing import NewType
from uuid import UUID

UserId = NewType("UserId", UUID)
RepositoryId = NewType("RepositoryId", UUID)
PredictionId = NewType("PredictionId", UUID)
CommitSha = NewType("CommitSha", str)


def validate_sha(sha: str) -> CommitSha:
    if len(sha) not in (7, 40):
        msg = f"Invalid commit SHA length: {len(sha)}"
        raise ValueError(msg)
    if not all(c in "0123456789abcdef" for c in sha.lower()):
        msg = f"Invalid commit SHA characters: {sha}"
        raise ValueError(msg)
    return CommitSha(sha.lower())
