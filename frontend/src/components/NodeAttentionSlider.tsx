import type { XAIReport } from "../api/types";
import { Slider } from "./ui/Slider";

export function NodeAttentionSlider({ report }: { report: XAIReport }) {
  if (!report.node_attentions.length) {
    return <p className="font-mono text-sm text-ink-500">No node attention data.</p>;
  }

  return (
    <Slider title="GNN Node Attention" subtitle="Slide — Attention" itemWidth="min(88vw, 260px)">
      {report.node_attentions.map((node) => (
        <article key={node.node_id} className="panel panel-hover h-40 p-5">
          <p className="font-mono text-[10px] text-ink-400">#{String(node.rank).padStart(2, "0")}</p>
          <p className="mt-2 font-heading text-lg font-semibold text-ink-900">{node.name}</p>
          {node.file_path && (
            <p className="mt-1 truncate font-mono text-[11px] text-ink-500">{node.file_path}</p>
          )}
          <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-ink-200">
            <div
              className="h-full rounded-full bg-ink-900"
              style={{ width: `${node.attention_score * 100}%` }}
            />
          </div>
          <p className="mt-2 font-heading text-xl font-bold text-ink-900">
            {(node.attention_score * 100).toFixed(0)}%
          </p>
        </article>
      ))}
    </Slider>
  );
}
