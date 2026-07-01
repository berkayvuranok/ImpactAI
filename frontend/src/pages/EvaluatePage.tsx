import { FormEvent, useEffect, useState } from "react";
import { api } from "../api/client";
import type { EvaluationReport, MetricTargets } from "../api/types";
import { PageHero } from "../components/ui/PageHero";
import { ScrollSection } from "../components/ui/ScrollSection";
import { StatGrid } from "../components/ui/StatGrid";

export function EvaluatePage() {
  const [targets, setTargets] = useState<MetricTargets | null>(null);
  const [reports, setReports] = useState<EvaluationReport[]>([]);
  const [latest, setLatest] = useState<EvaluationReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    const [t, list] = await Promise.all([api.getMetricTargets(), api.listEvaluationReports()]);
    setTargets(t);
    setReports(list.items);
    setLatest(list.items[0] ?? null);
  };

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Load failed"));
  }, []);

  const handleRun = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const report = await api.runBenchmark();
      setLatest(report);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Benchmark failed");
    } finally {
      setLoading(false);
    }
  };

  const metrics = latest?.aggregate_metrics;
  const statItems = metrics
    ? [
        { label: "F1", value: (metrics.f1 ?? 0).toFixed(2) },
        { label: "Prec@K", value: (metrics.precision_at_k ?? 0).toFixed(2) },
        { label: "Recall@K", value: (metrics.recall_at_k ?? 0).toFixed(2) },
        { label: "Risk RMSE", value: (metrics.risk_rmse ?? 0).toFixed(1) },
      ]
    : [];

  return (
    <div>
      <PageHero
        eyebrow="Evaluation"
        title="Measure model quality against golden benchmarks."
        description="Run the default benchmark suite, compare metrics to production targets, and track evaluation history."
      >
        <form onSubmit={handleRun}>
          <button type="submit" disabled={loading} className="btn-primary">
            {loading ? "Running benchmark…" : "Run benchmark →"}
          </button>
        </form>
      </PageHero>

      {error && (
        <div className="mb-6 panel px-4 py-3 font-mono text-sm text-ink-600">{error}</div>
      )}

      {latest && (
        <ScrollSection>
          <div className="mb-4 flex items-center gap-3">
            <span
              className={`rounded-full border px-3 py-1 font-mono text-[11px] uppercase tracking-widest ${
                latest.passed ? "border-ink-700 text-ink-900" : "border-ink-400 text-ink-500"
              }`}
            >
              {latest.passed ? "Passed" : "Below targets"}
            </span>
            <span className="font-mono text-xs text-ink-500">{latest.benchmark_name}</span>
          </div>
          {statItems.length > 0 && <StatGrid items={statItems} />}
        </ScrollSection>
      )}

      {targets && (
        <ScrollSection delay={100}>
          <section className="panel p-8">
            <p className="section-label">Production Targets</p>
            <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {Object.entries(targets).map(([key, val]) => (
                <div key={key} className="rounded-xl border border-ink-300 px-4 py-3">
                  <p className="font-mono text-[10px] uppercase tracking-widest text-ink-500">
                    {key.replace(/_/g, " ")}
                  </p>
                  <p className="font-heading text-xl font-bold text-ink-900">{val}</p>
                </div>
              ))}
            </div>
          </section>
        </ScrollSection>
      )}

      {latest && latest.sample_results.length > 0 && (
        <ScrollSection delay={150}>
          <p className="section-label mb-4">Sample Breakdown</p>
          <div className="space-y-3">
            {latest.sample_results.map((s) => (
              <div key={s.sample_id} className="panel flex flex-wrap items-center justify-between gap-4 px-5 py-4">
                <div>
                  <p className="font-heading font-semibold text-ink-900">{s.sample_id}</p>
                  <p className="text-sm text-ink-500">{s.description}</p>
                </div>
                <span className="font-mono text-xs text-ink-500">
                  F1 {(s.metrics.f1 ?? 0).toFixed(2)} · MAE {(s.metrics.risk_mae ?? 0).toFixed(1)}
                </span>
              </div>
            ))}
          </div>
        </ScrollSection>
      )}

      {reports.length > 1 && (
        <ScrollSection delay={200}>
          <p className="section-label mb-4">History ({reports.length} reports)</p>
          <div className="space-y-2">
            {reports.slice(0, 5).map((r) => (
              <div key={r.id} className="panel px-4 py-3 font-mono text-xs text-ink-500">
                {r.created_at.slice(0, 19)} · {r.benchmark_name} ·{" "}
                {r.passed ? "PASS" : "FAIL"}
              </div>
            ))}
          </div>
        </ScrollSection>
      )}
    </div>
  );
}
