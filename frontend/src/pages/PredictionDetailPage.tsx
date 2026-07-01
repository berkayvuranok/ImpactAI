import { useCallback } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import { AffectedFilesList } from "../components/AffectedFilesList";
import { DependencyGraph } from "../components/DependencyGraph";
import { RiskGauge } from "../components/RiskGauge";
import { usePolling } from "../hooks/usePolling";

export function PredictionDetailPage() {
  const { id } = useParams<{ id: string }>();

  const fetcher = useCallback(() => {
    if (!id) throw new Error("Missing prediction id");
    return api.getPrediction(id);
  }, [id]);

  const shouldPoll = useCallback(
    (data: { status: string }) => data.status === "pending" || data.status === "running",
    [],
  );

  const { data: prediction, error, loading } = usePolling(fetcher, 2000, shouldPoll);

  if (loading && !prediction) {
    return <p className="text-slate-500">Loading prediction…</p>;
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-900/50 bg-red-950/30 px-4 py-3 text-red-300">
        {error}
      </div>
    );
  }

  if (!prediction) return null;

  const isPending = prediction.status === "pending" || prediction.status === "running";
  const riskScore = (prediction.risk_score ?? 0) * 100;
  const topFiles = prediction.affected_files.slice(0, 5).map((f) => f.file_path);

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link to="/predict" className="text-sm text-brand-400 hover:underline">
            ← Back to predict
          </Link>
          <h2 className="mt-2 text-2xl font-semibold text-white">Prediction result</h2>
          <p className="mt-1 font-mono text-xs text-slate-500">{prediction.id}</p>
        </div>
        <span
          className={`rounded-full px-3 py-1 text-xs font-medium uppercase ${
            prediction.status === "completed"
              ? "bg-green-950 text-green-400"
              : prediction.status === "failed"
                ? "bg-red-950 text-red-400"
                : "bg-amber-950 text-amber-400"
          }`}
        >
          {prediction.status}
          {isPending && " (polling…)"}
        </span>
      </div>

      {prediction.error_message && (
        <div className="rounded-lg border border-red-900/50 bg-red-950/30 px-4 py-3 text-sm text-red-300">
          {prediction.error_message}
        </div>
      )}

      {prediction.status === "completed" && (
        <>
          <div className="grid gap-6 lg:grid-cols-[auto_1fr]">
            <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
              <RiskGauge score={riskScore} />
              <div className="mt-4 space-y-2 text-center text-sm text-slate-400">
                <p>
                  Regression:{" "}
                  <span className="text-white">
                    {((prediction.regression_probability ?? 0) * 100).toFixed(0)}%
                  </span>
                </p>
                <p>
                  Confidence:{" "}
                  <span className="text-white">
                    {((prediction.confidence_score ?? 0) * 100).toFixed(0)}%
                  </span>
                </p>
              </div>
            </div>

            {prediction.explanation && (
              <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
                <h3 className="font-medium text-white">Explanation</h3>
                <div className="mt-4 space-y-3 text-sm text-slate-300">
                  <p>
                    <span className="text-slate-500">Root cause: </span>
                    {prediction.explanation.root_cause}
                  </p>
                  <p>
                    <span className="text-slate-500">Risk: </span>
                    {prediction.explanation.risk_explanation}
                  </p>
                  <p>
                    <span className="text-slate-500">Affected files: </span>
                    {prediction.explanation.affected_files_explanation}
                  </p>
                </div>
              </div>
            )}
          </div>

          <section>
            <h3 className="mb-4 font-medium text-white">Affected files</h3>
            <AffectedFilesList files={prediction.affected_files} />
          </section>

          {prediction.suggested_reviewers.length > 0 && (
            <section>
              <h3 className="mb-4 font-medium text-white">Suggested reviewers</h3>
              <div className="grid gap-3 sm:grid-cols-2">
                {prediction.suggested_reviewers.map((r) => (
                  <div
                    key={r.user_id}
                    className="rounded-lg border border-slate-800 bg-slate-900/60 p-4"
                  >
                    <p className="font-medium text-white">{r.username}</p>
                    <p className="text-sm text-brand-400">Score {(r.score * 100).toFixed(0)}%</p>
                    {r.rationale && <p className="mt-2 text-xs text-slate-400">{r.rationale}</p>}
                  </div>
                ))}
              </div>
            </section>
          )}

          {topFiles.length > 0 && (
            <SubgraphSection repositoryId={prediction.repository_id} files={topFiles} />
          )}
        </>
      )}
    </div>
  );
}

function SubgraphSection({ repositoryId, files }: { repositoryId: string; files: string[] }) {
  const filesKey = files.join("\n");
  const fetcher = useCallback(
    () => api.getSubgraph(repositoryId, files),
    [repositoryId, filesKey],
  );
  const { data, loading } = usePolling(fetcher, 0, () => false);

  if (loading) return <p className="text-sm text-slate-500">Loading subgraph…</p>;
  if (!data) return null;

  return (
    <section>
      <h3 className="mb-4 font-medium text-white">Impact subgraph</h3>
      <DependencyGraph snapshot={data} />
    </section>
  );
}
