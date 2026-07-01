import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import type { Repository } from "../api/types";
import { DependencyGraph } from "../components/DependencyGraph";

export function GraphPage() {
  const [searchParams] = useSearchParams();
  const [repos, setRepos] = useState<Repository[]>([]);
  const [repositoryId, setRepositoryId] = useState(searchParams.get("repo") ?? "");
  const [seedFiles, setSeedFiles] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [snapshot, setSnapshot] = useState<Awaited<ReturnType<typeof api.getGraph>> | null>(null);

  useEffect(() => {
    api.listRepositories().then((r) => {
      setRepos(r.items);
      if (!repositoryId && r.items.length) {
        setRepositoryId(r.items[0].id);
      }
    });
  }, [repositoryId]);

  const loadFullGraph = async () => {
    if (!repositoryId) return;
    setLoading(true);
    setError(null);
    try {
      setSnapshot(await api.getGraph(repositoryId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load graph");
      setSnapshot(null);
    } finally {
      setLoading(false);
    }
  };

  const loadSubgraph = async () => {
    if (!repositoryId) return;
    const files = seedFiles
      .split("\n")
      .map((f) => f.trim())
      .filter(Boolean);
    if (!files.length) {
      setError("Enter at least one seed file path");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setSnapshot(await api.getSubgraph(repositoryId, files));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load subgraph");
      setSnapshot(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold text-white">Dependency graph</h2>
        <p className="mt-1 text-slate-400">Visualize repository structure and impact neighborhoods.</p>
      </div>

      <div className="grid gap-4 rounded-xl border border-slate-800 bg-slate-900/50 p-6 lg:grid-cols-2">
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

        <div className="flex items-end gap-2">
          <button
            type="button"
            onClick={loadFullGraph}
            disabled={loading || !repositoryId}
            className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-500 disabled:opacity-50"
          >
            Load full graph
          </button>
        </div>

        <label className="block lg:col-span-2">
          <span className="text-sm text-slate-400">Seed files (one per line, for subgraph)</span>
          <textarea
            rows={3}
            value={seedFiles}
            onChange={(e) => setSeedFiles(e.target.value)}
            placeholder="src/main.py&#10;src/utils/helpers.py"
            className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 font-mono text-sm text-white"
          />
        </label>

        <div className="lg:col-span-2">
          <button
            type="button"
            onClick={loadSubgraph}
            disabled={loading || !repositoryId}
            className="rounded-lg border border-slate-700 px-4 py-2 text-sm text-slate-300 hover:border-brand-500 disabled:opacity-50"
          >
            Load subgraph
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-red-900/50 bg-red-950/30 px-4 py-3 text-sm text-red-300">
          {error}
        </div>
      )}

      {loading && <p className="text-sm text-slate-500">Loading graph…</p>}

      {snapshot && !loading && (
        <div>
          <p className="mb-2 text-sm text-slate-500">
            {snapshot.node_count} nodes · {snapshot.edge_count} edges · commit{" "}
            <span className="font-mono">{snapshot.commit_sha.slice(0, 8)}</span>
          </p>
          <DependencyGraph snapshot={snapshot} height="600px" />
        </div>
      )}
    </div>
  );
}
