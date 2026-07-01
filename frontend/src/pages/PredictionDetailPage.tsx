import { useCallback } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import { AffectedFilesList } from "../components/AffectedFilesList";
import { DependencyGraph } from "../components/DependencyGraph";
import { RiskGauge } from "../components/RiskGauge";
import { PageHero } from "../components/ui/PageHero";
import { ScrollSection } from "../components/ui/ScrollSection";
import { Slider } from "../components/ui/Slider";
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
    return (
      <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4">
        <div className="h-12 w-12 animate-spin rounded-full border-2 border-ink-400 border-t-ink-900" />
        <p className="font-mono text-sm text-ink-500">Running prediction pipeline…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="panel px-6 py-4 font-mono text-sm text-ink-700">{error}</div>
    );
  }

  if (!prediction) return null;

  const isPending = prediction.status === "pending" || prediction.status === "running";
  const riskScore = (prediction.risk_score ?? 0) * 100;
  const topFiles = prediction.affected_files.slice(0, 5).map((f) => f.file_path);

  return (
    <div>
      <PageHero
        eyebrow="Prediction Result"
        title={isPending ? "Analysis in progress…" : "Impact report ready."}
        description={prediction.id}
      >
        <span
          className={`inline-flex rounded-full border px-4 py-1.5 font-mono text-[11px] uppercase tracking-widest ${
            prediction.status === "completed"
              ? "border-ink-700 text-ink-900"
              : prediction.status === "failed"
                ? "border-ink-400 text-ink-500 line-through"
                : "border-ink-500 text-ink-600"
          }`}
        >
          {prediction.status}
          {isPending && " · polling"}
        </span>
      </PageHero>

      <Link to="/predict" className="mb-8 inline-block font-mono text-xs text-ink-500 hover:text-ink-800">
        ← Back to predict
      </Link>

      {prediction.error_message && (
        <div className="mb-8 panel px-6 py-4 font-mono text-sm text-ink-600">
          {prediction.error_message}
        </div>
      )}

      {prediction.status === "completed" && (
        <>
          <ScrollSection>
            <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
              <div className="panel flex flex-col items-center p-8">
                <RiskGauge score={riskScore} />
                <div className="mt-6 w-full space-y-3 border-t border-ink-300 pt-6 text-center">
                  <Metric
                    label="Regression"
                    value={`${((prediction.regression_probability ?? 0) * 100).toFixed(0)}%`}
                  />
                  <Metric
                    label="Confidence"
                    value={`${((prediction.confidence_score ?? 0) * 100).toFixed(0)}%`}
                  />
                </div>
              </div>

              {prediction.explanation && (
                <div className="panel p-8">
                  <p className="section-label">LLM Explanation</p>
                  <div className="mt-6 space-y-6">
                    <ExplainBlock title="Root cause" text={prediction.explanation.root_cause} />
                    <ExplainBlock title="Risk" text={prediction.explanation.risk_explanation} />
                    <ExplainBlock
                      title="Affected files"
                      text={prediction.explanation.affected_files_explanation}
                    />
                  </div>
                </div>
              )}
            </div>
          </ScrollSection>

          <ScrollSection delay={100}>
            <p className="section-label mb-4">Affected Files</p>
            <AffectedFilesList files={prediction.affected_files} />
          </ScrollSection>

          {prediction.suggested_reviewers.length > 0 && (
            <ScrollSection delay={150}>
              <Slider
                title="Suggested Reviewers"
                subtitle="Slide — Reviewers"
                itemWidth="min(88vw, 280px)"
              >
                {prediction.suggested_reviewers.map((r) => (
                  <article key={r.user_id} className="panel panel-hover h-44 p-6">
                    <p className="font-heading text-xl font-semibold text-ink-900">{r.username}</p>
                    <p className="mt-2 font-heading text-3xl font-bold text-ink-900">
                      {(r.score * 100).toFixed(0)}%
                    </p>
                    {r.rationale && (
                      <p className="mt-3 line-clamp-2 text-xs leading-relaxed text-ink-500">
                        {r.rationale}
                      </p>
                    )}
                  </article>
                ))}
              </Slider>
            </ScrollSection>
          )}

          {topFiles.length > 0 && (
            <ScrollSection delay={200}>
              <SubgraphSection repositoryId={prediction.repository_id} files={topFiles} />
            </ScrollSection>
          )}
        </>
      )}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="font-mono text-[10px] uppercase tracking-widest text-ink-500">{label}</p>
      <p className="font-heading text-2xl font-bold text-ink-900">{value}</p>
    </div>
  );
}

function ExplainBlock({ title, text }: { title: string; text: string }) {
  return (
    <div>
      <p className="font-mono text-[10px] uppercase tracking-widest text-ink-500">{title}</p>
      <p className="mt-2 leading-relaxed text-ink-700">{text}</p>
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

  if (loading) {
    return <p className="font-mono text-sm text-ink-500">Loading impact subgraph…</p>;
  }
  if (!data) return null;

  return (
    <section>
      <p className="section-label mb-2">Impact Subgraph</p>
      <h3 className="mb-6 font-heading text-2xl font-semibold text-ink-900">
        Dependency neighborhood
      </h3>
      <DependencyGraph snapshot={data} />
    </section>
  );
}
