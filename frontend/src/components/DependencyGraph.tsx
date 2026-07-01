import { useMemo } from "react";
import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  type Edge,
  type Node,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import type { GraphSnapshot } from "../api/types";

const TYPE_COLORS: Record<string, string> = {
  file: "#22d3ee",
  module: "#06b6d4",
  class: "#8b5cf6",
  function: "#a78bfa",
  package: "#64748b",
};

function layoutNodes(snapshot: GraphSnapshot): Node[] {
  const cols = Math.ceil(Math.sqrt(snapshot.nodes.length)) || 1;
  return snapshot.nodes.map((node, index) => ({
    id: node.node_id,
    position: {
      x: (index % cols) * 220,
      y: Math.floor(index / cols) * 100,
    },
    data: {
      label: (
        <div className="text-xs">
          <p className="font-mono font-medium text-white">{node.name}</p>
          {node.file_path && <p className="truncate text-slate-400">{node.file_path}</p>}
        </div>
      ),
    },
    style: {
      background: "#0f172a",
      border: `1px solid ${TYPE_COLORS[node.node_type] ?? "#475569"}`,
      borderRadius: 8,
      padding: 8,
      width: 180,
      color: "#e2e8f0",
    },
  }));
}

function toEdges(snapshot: GraphSnapshot): Edge[] {
  return snapshot.edges.map((edge, index) => ({
    id: `${edge.source_id}-${edge.target_id}-${index}`,
    source: edge.source_id,
    target: edge.target_id,
    label: edge.edge_type,
    animated: edge.weight > 0.5,
    style: { stroke: "#475569" },
    labelStyle: { fill: "#94a3b8", fontSize: 10 },
  }));
}

interface DependencyGraphProps {
  snapshot: GraphSnapshot;
  height?: string;
}

export function DependencyGraph({ snapshot, height = "520px" }: DependencyGraphProps) {
  const nodes = useMemo(() => layoutNodes(snapshot), [snapshot]);
  const edges = useMemo(() => toEdges(snapshot), [snapshot]);

  if (!snapshot.nodes.length) {
    return (
      <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-8 text-center text-slate-500">
        No graph data. Sync a repository and build its dependency graph first.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-slate-800" style={{ height }}>
      <ReactFlow nodes={nodes} edges={edges} fitView minZoom={0.2} maxZoom={1.5}>
        <Background color="#334155" gap={20} />
        <Controls />
        <MiniMap
          nodeColor={(n) => TYPE_COLORS[(n.data as { nodeType?: string }).nodeType ?? "file"] ?? "#475569"}
          maskColor="rgba(15, 23, 42, 0.8)"
        />
      </ReactFlow>
    </div>
  );
}
