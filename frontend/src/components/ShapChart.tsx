import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { XAIReport } from "../api/types";

export function ShapChart({ report }: { report: XAIReport }) {
  const data = [...report.feature_attributions]
    .sort((a, b) => Math.abs(b.shap_value) - Math.abs(a.shap_value))
    .slice(0, 8)
    .map((f) => ({
      name: f.label || f.feature,
      shap: Number(f.shap_value.toFixed(2)),
    }));

  if (!data.length) {
    return <p className="font-mono text-sm text-ink-500">No SHAP attributions available.</p>;
  }

  return (
    <div className="h-72">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16 }}>
          <CartesianGrid stroke="#262626" horizontal={false} />
          <XAxis type="number" stroke="#525252" fontSize={10} tickLine={false} />
          <YAxis
            type="category"
            dataKey="name"
            width={120}
            stroke="#525252"
            fontSize={10}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              background: "#111",
              border: "1px solid #404040",
              borderRadius: 12,
              fontFamily: "IBM Plex Mono",
              fontSize: 11,
            }}
          />
          <Bar dataKey="shap" fill="#fafafa" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
