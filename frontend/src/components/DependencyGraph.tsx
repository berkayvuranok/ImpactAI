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

const TYPE_STROKES: Record<string, string> = {
  file: "#ffffff",
  module: "#d4d4d4",
  class: "#a3a3a3",
  function: "#737373",
  package: "#404040",
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
          <p className="font-mono font-medium text-ink-900">{node.name}</p>
          {node.file_path && <p className="truncate text-ink-500">{node.file_path}</p>}
        </div>
      ),
    },
    style: {
      background: "#0a0a0a",
      border: `1px solid ${TYPE_STROKES[node.node_type] ?? "#404040"}`,
      borderRadius: 12,
      padding: 10,
      width: 180,
      color: "#fafafa",
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
    style: { stroke: "#525252" },
    labelStyle: { fill: "#737373", fontSize: 10 },
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
      <div className="panel p-12 text-center font-mono text-sm text-ink-500">
        No graph data. Sync a repository and build its dependency graph first.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-ink-300" style={{ height }}>
      <ReactFlow nodes={nodes} edges={edges} fitView minZoom={0.2} maxZoom={1.5} colorMode="dark">
        <Background color="#262626" gap={24} size={1} />
        <Controls />
        <MiniMap nodeColor="#404040" maskColor="rgba(0,0,0,0.85)" />
      </ReactFlow>
    </div>
  );
}
