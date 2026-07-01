import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import type { Repository } from "../api/types";

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

export function PredictPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [repos, setRepos] = useState<Repository[]>([]);
  const [repositoryId, setRepositoryId] = useState(searchParams.get("repo") ?? "");
  const [diff, setDiff] = useState(SAMPLE_DIFF);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.listRepositories().then((r) => {
      setRepos(r.items);
      if (!repositoryId && r.items.length) {
        setRepositoryId(r.items[0].id);
      }
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
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold text-white">Predict impact</h2>
        <p className="mt-1 text-slate-400">Submit a unified diff to analyze regression risk.</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <label className="block">
          <span className="text-sm text-slate-400">Repository</span>
          <select
            value={repositoryId}
            onChange={(e) => setRepositoryId(e.target.value)}
            className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white"
          >
            <option value="">Select…</option>
            {repos.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name}
              </option>
            ))}
          </select>
        </label>

        <label className="block">
          <span className="text-sm text-slate-400">Unified diff</span>
          <textarea
            rows={16}
            required
            value={diff}
            onChange={(e) => setDiff(e.target.value)}
            className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 font-mono text-sm text-white"
          />
        </label>

        {error && <p className="text-sm text-red-400">{error}</p>}

        <div className="flex gap-3">
          <button
            type="submit"
            disabled={loading}
            className="rounded-lg bg-brand-600 px-5 py-2.5 font-medium text-white hover:bg-brand-500 disabled:opacity-50"
          >
            {loading ? "Submitting…" : "Run prediction"}
          </button>
          <Link
            to="/"
            className="rounded-lg border border-slate-700 px-5 py-2.5 text-slate-300 hover:border-slate-500"
          >
            Cancel
          </Link>
        </div>
      </form>
    </div>
  );
}
