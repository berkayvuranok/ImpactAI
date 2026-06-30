"""Build repository dependency graphs from AST and Git sources."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from code_impact.domain.entities import GraphEdge, GraphNode, GraphSnapshot
from code_impact.domain.services import DiffAnalysisResult, IGraphBuilder
from code_impact.domain.services.git_service import IGitService
from code_impact.domain.value_objects.enums import EdgeType, NodeType
from code_impact.infrastructure.analysis.language_detector import detect_language
from code_impact.infrastructure.analysis.structure_analyzer import StructureAnalyzer
from code_impact.infrastructure.graph.import_resolver import parse_import_modules, resolve_module_to_file
from code_impact.infrastructure.graph.node_ids import (
    class_id,
    file_id,
    function_id,
    module_id,
    service_id,
)


@dataclass
class GraphBuildState:
    nodes: dict[str, GraphNode] = field(default_factory=dict)
    edges: list[tuple[str, str, EdgeType, float, dict]] = field(default_factory=list)

    def add_node(
        self,
        snapshot_id: UUID,
        node_id: str,
        node_type: NodeType,
        name: str,
        file_path: str | None = None,
        properties: dict | None = None,
    ) -> None:
        if node_id in self.nodes:
            return
        self.nodes[node_id] = GraphNode(
            id=uuid4(),
            snapshot_id=snapshot_id,
            node_id=node_id,
            node_type=node_type,
            name=name,
            file_path=file_path,
            properties=properties or {},
        )

    def add_edge(
        self,
        source: str,
        target: str,
        edge_type: EdgeType,
        weight: float = 1.0,
        properties: dict | None = None,
    ) -> None:
        key = (source, target, edge_type)
        if any(e[0] == key[0] and e[1] == key[1] and e[2] == edge_type for e in self.edges):
            return
        self.edges.append((source, target, edge_type, weight, properties or {}))


class DependencyGraphBuilder(IGraphBuilder):
    """Constructs multi-layer dependency graphs for GNN consumption."""

    def __init__(
        self,
        git_service: IGitService,
        structure_analyzer: StructureAnalyzer | None = None,
    ) -> None:
        self._git = git_service
        self._structure = structure_analyzer or StructureAnalyzer()

    async def build_from_repository(
        self,
        repository_id: UUID,
        commit_sha: str,
    ) -> GraphSnapshot:
        snapshot_id = uuid4()
        state = GraphBuildState()

        file_paths = await self._git.list_source_files(repository_id, commit_sha)
        file_path_set = set(file_paths)

        for path in file_paths:
            await self._process_file(repository_id, commit_sha, path, snapshot_id, state, file_path_set)

        self._detect_services(file_paths, snapshot_id, state)
        self._link_service_files(file_paths, snapshot_id, state)

        nodes = list(state.nodes.values())
        edges = [
            GraphEdge(
                id=uuid4(),
                snapshot_id=snapshot_id,
                source_id=src,
                target_id=tgt,
                edge_type=etype,
                weight=weight,
                properties=props,
            )
            for src, tgt, etype, weight, props in state.edges
        ]

        return GraphSnapshot(
            id=snapshot_id,
            repository_id=repository_id,
            commit_sha=commit_sha,
            node_count=len(nodes),
            edge_count=len(edges),
            storage_path="",
            nodes=nodes,
            edges=edges,
        )

    async def apply_diff_delta(
        self,
        snapshot: GraphSnapshot,
        diff_result: DiffAnalysisResult,
    ) -> GraphSnapshot:
        """Incrementally rebuild nodes/edges for changed files."""
        state = GraphBuildState()
        for node in snapshot.nodes:
            state.nodes[node.node_id] = node
        for edge in snapshot.edges:
            state.edges.append(
                (edge.source_id, edge.target_id, edge.edge_type, edge.weight, edge.properties)
            )

        file_path_set = {n.file_path for n in snapshot.nodes if n.file_path and n.node_type == NodeType.FILE}
        file_path_set.update(diff_result.changed_files)

        for path in diff_result.changed_files:
            removed_ids = {n.node_id for n in state.nodes.values() if n.file_path == path}
            state.nodes = {k: v for k, v in state.nodes.items() if v.file_path != path}
            state.edges = [
                e for e in state.edges if e[0] not in removed_ids and e[1] not in removed_ids
            ]
            await self._process_file(
                snapshot.repository_id,
                snapshot.commit_sha,
                path,
                snapshot.id,
                state,
                file_path_set,
            )

        nodes = list(state.nodes.values())
        edges = [
            GraphEdge(
                id=uuid4(),
                snapshot_id=snapshot.id,
                source_id=src,
                target_id=tgt,
                edge_type=etype,
                weight=weight,
                properties=props,
            )
            for src, tgt, etype, weight, props in state.edges
        ]

        return GraphSnapshot(
            id=snapshot.id,
            repository_id=snapshot.repository_id,
            commit_sha=snapshot.commit_sha,
            node_count=len(nodes),
            edge_count=len(edges),
            storage_path=snapshot.storage_path,
            nodes=nodes,
            edges=edges,
        )

    async def _process_file(
        self,
        repository_id: UUID,
        commit_sha: str,
        path: str,
        snapshot_id: UUID,
        state: GraphBuildState,
        file_path_set: set[str],
    ) -> None:
        content = await self._git.get_file_content(repository_id, commit_sha, path)
        if content is None:
            return

        language = detect_language(path)
        fid = file_id(path)
        state.add_node(snapshot_id, fid, NodeType.FILE, path, file_path=path, properties={"language": language})

        structure = self._structure.analyze(content, language)

        for cls in structure.classes:
            cid = class_id(path, cls.name)
            state.add_node(snapshot_id, cid, NodeType.CLASS, cls.name, file_path=path)
            state.add_edge(fid, cid, EdgeType.COMPOSITION, properties={"relationship": "contains"})

        for fn in structure.functions:
            fnid = function_id(path, fn.qualified_name)
            state.add_node(snapshot_id, fnid, NodeType.FUNCTION, fn.qualified_name, file_path=path)
            if "." in fn.qualified_name:
                parent_class = fn.qualified_name.split(".")[0]
                state.add_edge(class_id(path, parent_class), fnid, EdgeType.COMPOSITION)
            else:
                state.add_edge(fid, fnid, EdgeType.COMPOSITION)

        for import_line in structure.imports:
            for module in parse_import_modules(import_line):
                mid = module_id(module)
                state.add_node(snapshot_id, mid, NodeType.MODULE, module)
                state.add_edge(fid, mid, EdgeType.IMPORT, properties={"import": import_line})

                resolved = resolve_module_to_file(module, file_path_set)
                if resolved and resolved != path:
                    state.add_edge(fid, file_id(resolved), EdgeType.IMPORT, weight=2.0, properties={"resolved": True})

        for class_name, bases in structure.inheritance:
            cid = class_id(path, class_name)
            for base in bases:
                target = self._resolve_symbol(base, path, state)
                if target:
                    state.add_edge(cid, target, EdgeType.INHERITANCE)

        for caller, callee in structure.calls:
            source = function_id(path, caller) if caller != "<module>" else fid
            target = self._resolve_symbol(callee, path, state)
            if target and target != source:
                state.add_edge(source, target, EdgeType.CALL)

        for api in structure.api_targets:
            ext = service_id(f"api:{api}")
            state.add_node(snapshot_id, ext, NodeType.SERVICE, f"api:{api}")
            state.add_edge(fid, ext, EdgeType.API_CALL)

        for db in structure.db_targets:
            ext = service_id(f"db:{db}")
            state.add_node(snapshot_id, ext, NodeType.SERVICE, f"db:{db}")
            state.add_edge(fid, ext, EdgeType.DATABASE_ACCESS)

        for mq in structure.mq_targets:
            ext = service_id(f"mq:{mq}")
            state.add_node(snapshot_id, ext, NodeType.SERVICE, f"mq:{mq}")
            state.add_edge(fid, ext, EdgeType.MESSAGE_QUEUE)

    def _resolve_symbol(self, symbol: str, file_path: str, state: GraphBuildState) -> str | None:
        simple = symbol.split(".")[-1]
        candidates = [
            nid
            for nid, node in state.nodes.items()
            if node.file_path == file_path
            and node.node_type in (NodeType.FUNCTION, NodeType.CLASS)
            and (node.name == symbol or node.name.endswith(f".{simple}") or node.name == simple)
        ]
        if candidates:
            return candidates[0]

        for nid, node in state.nodes.items():
            if node.node_type in (NodeType.FUNCTION, NodeType.CLASS) and node.name == simple:
                return nid
        return None

    def _detect_services(self, file_paths: list[str], snapshot_id: UUID, state: GraphBuildState) -> None:
        for path in file_paths:
            parts = path.split("/")
            for part in parts:
                if part.endswith("Service") or part.endswith("_service"):
                    sid = service_id(part)
                    state.add_node(snapshot_id, sid, NodeType.SERVICE, part)

    def _link_service_files(self, file_paths: list[str], snapshot_id: UUID, state: GraphBuildState) -> None:
        for path in file_paths:
            if "/services/" in path or "service" in path.lower():
                fid = file_id(path)
                service_name = next(
                    (p for p in path.split("/") if "service" in p.lower()),
                    None,
                )
                if service_name:
                    sid = service_id(service_name)
                    if sid in state.nodes:
                        state.add_edge(fid, sid, EdgeType.MICROSERVICE)
