import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import type { Repository } from "../api/types";
import { PageHero } from "../components/ui/PageHero";
import { ScrollSection } from "../components/ui/ScrollSection";

const SAMPLE_DIFF = `diff --git a/src/example.py b/src/example.py
index abc123..def456 100644
--- a/src/example.py
+++ b/src/example.py
@@ -1,3 +1,4 @@
 def hello():
-    return "world"
+    return "universe"
+
+def goodbye():
+    return "bye"
`;

const STEPS = [
  { n: "01", t: "Select repo", d: "Choose the target repository from your connected list." },
  { n: "02", t: "Paste diff", d: "Unified diff format — the same output as git diff." },
  { n: "03", t: "Analyze", d: "GNN + ML ensemble scores risk and ranks affected files." },
];

export function PredictPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [repos, setRepos] = useState<Repository[]>([]);
  const [repositoryId, setRepositoryId] = useState(searchParams.get("repo") ?? "");
  const [diff, setDiff] = useState(SAMPLE_DIFF);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [step, setStep] = useState(0);

  useEffect(() => {
    api.listRepositories().then((r) => {
      setRepos(r.items);
      if (!repositoryId && r.items.length) setRepositoryId(r.items[0].id);
    });
  }, [repositoryId]);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!repositoryId) {
      setError("Select a repository");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const accepted = await api.predict(repositoryId, diff);
      navigate(`/prediction/${accepted.prediction_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Prediction failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <PageHero
        eyebrow="Impact Analysis"
        title="Submit a diff. Get risk intelligence."
        description="The pipeline parses your change, walks the dependency graph, and returns a calibrated regression score with explanations."
      />

      <ScrollSection>
        <div className="mb-10 flex gap-4 overflow-x-auto pb-2">
          {STEPS.map((s, i) => (
            <button
              key={s.n}
              type="button"
              onClick={() => setStep(i)}
              className={`panel shrink-0 px-6 py-4 text-left transition ${
                step === i ? "border-ink-700 bg-ink-200/50" : "panel-hover"
              }`}
              style={{ minWidth: 220 }}
            >
              <span className="font-mono text-[10px] text-ink-400">{s.n}</span>
              <p className="mt-1 font-heading font-semibold text-ink-900">{s.t}</p>
              <p className="mt-1 text-xs text-ink-500">{s.d}</p>
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="panel p-8 md:p-10">
          <div className={`space-y-6 ${step !== 0 ? "hidden md:block md:space-y-6" : ""}`}>
            <label className="block">
              <span className="section-label">Repository</span>
              <select
                value={repositoryId}
                onChange={(e) => setRepositoryId(e.target.value)}
                className="input-field mt-2"
              >
                <option value="">Select…</option>
                {repos.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.name}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div className={`mt-6 ${step === 1 || step === 2 ? "" : "hidden md:block"}`}>
            <label className="block">
              <span className="section-label">Unified Diff</span>
              <textarea
                rows={18}
                required
                value={diff}
                onChange={(e) => setDiff(e.target.value)}
                className="input-field mt-2 font-mono text-[13px] leading-relaxed"
              />
            </label>
          </div>

          {error && (
            <p className="mt-4 font-mono text-sm text-ink-600">{error}</p>
          )}

          <div className="mt-8 flex flex-wrap items-center gap-4">
            <button type="submit" disabled={loading} className="btn-primary">
              {loading ? "Analyzing…" : "Run prediction →"}
            </button>
            <Link to="/" className="btn-ghost">
              Cancel
            </Link>
            <div className="ml-auto hidden items-center gap-2 font-mono text-[10px] uppercase tracking-widest text-ink-500 sm:flex">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-ink-700" />
              Async pipeline · ~30s
            </div>
          </div>
        </form>
      </ScrollSection>
    </div>
  );
}
