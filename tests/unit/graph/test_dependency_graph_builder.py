"""Unit tests for DependencyGraphBuilder."""

from pathlib import Path
from uuid import uuid4

import pytest

from code_impact.domain.value_objects.enums import EdgeType, NodeType
from code_impact.infrastructure.graph.dependency_graph_builder import DependencyGraphBuilder


class FakeGitService:
    def __init__(self, files: dict[str, str]):
        self._files = files
        self._repo_id = uuid4()

    def get_local_path(self, repository_id):
        return Path("/tmp/fake")

    async def list_source_files(self, repository_id, commit_sha):
        return sorted(self._files.keys())

    async def get_file_content(self, repository_id, commit_sha, file_path):
        return self._files.get(file_path)


SERVICE_PY = '''\
import httpx
from sqlalchemy.orm import Session

class UserService:
    def get_user(self, user_id: int):
        return self._fetch(user_id)

    def _fetch(self, user_id: int):
        httpx.get(f"https://api.example.com/users/{user_id}")
        return {"id": user_id}

class AdminService(UserService):
    def promote(self, user_id: int):
        return True
'''

UTILS_PY = '''\
def helper():
    return 42
'''

MAIN_PY = '''\
from app.service import UserService
from utils import helper

def main():
    svc = UserService()
    svc.get_user(1)
    return helper()
'''


@pytest.mark.asyncio
async def test_build_graph_nodes_and_edges():
    files = {
        "app/service.py": SERVICE_PY,
        "utils.py": UTILS_PY,
        "main.py": MAIN_PY,
    }
    builder = DependencyGraphBuilder(FakeGitService(files))
    repo_id = uuid4()
    snapshot = await builder.build_from_repository(repo_id, "abc123")

    assert snapshot.node_count > 0
    assert snapshot.edge_count > 0

    node_types = {n.node_type for n in snapshot.nodes}
    assert NodeType.FILE in node_types
    assert NodeType.CLASS in node_types
    assert NodeType.FUNCTION in node_types

    edge_types = {e.edge_type for e in snapshot.edges}
    assert EdgeType.IMPORT in edge_types
    assert EdgeType.COMPOSITION in edge_types
    assert EdgeType.INHERITANCE in edge_types
    assert EdgeType.API_CALL in edge_types
    assert EdgeType.DATABASE_ACCESS in edge_types


@pytest.mark.asyncio
async def test_build_graph_has_file_nodes():
    files = {"main.py": "def run(): pass\n"}
    builder = DependencyGraphBuilder(FakeGitService(files))
    snapshot = await builder.build_from_repository(uuid4(), "deadbeef")

    file_nodes = [n for n in snapshot.nodes if n.node_type == NodeType.FILE]
    assert len(file_nodes) == 1
    assert file_nodes[0].name == "main.py"
