import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import type { Repository } from "../api/types";
import { DependencyGraph } from "../components/DependencyGraph";
import { PageHero } from "../components/ui/PageHero";
import { ScrollSection } from "../components/ui/ScrollSection";

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
      if (!repositoryId && r.items.length) setRepositoryId(r.items[0].id);
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
    <div>
      <PageHero
        eyebrow="Dependency Graph"
        title="See how code connects."
        description="Explore the full repository graph or zoom into a BFS neighborhood around changed files."
      />

      <ScrollSection>
        <div className="panel p-8 md:p-10">
          <div className="grid gap-6 lg:grid-cols-2">
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

            <div className="flex items-end">
              <button
                type="button"
                onClick={loadFullGraph}
                disabled={loading || !repositoryId}
                className="btn-primary w-full sm:w-auto"
              >
                Load full graph
              </button>
            </div>

            <label className="block lg:col-span-2">
              <span className="section-label">Seed files (subgraph)</span>
              <textarea
                rows={4}
                value={seedFiles}
                onChange={(e) => setSeedFiles(e.target.value)}
                placeholder={"src/main.py\nsrc/utils/helpers.py"}
                className="input-field mt-2 font-mono text-[13px]"
              />
            </label>

            <div className="lg:col-span-2">
              <button
                type="button"
                onClick={loadSubgraph}
                disabled={loading || !repositoryId}
                className="btn-ghost"
              >
                Load subgraph
              </button>
            </div>
          </div>

          {error && (
            <p className="mt-6 font-mono text-sm text-ink-600">{error}</p>
          )}
        </div>
      </ScrollSection>

      {loading && (
        <div className="flex justify-center py-16">
          <div className="h-10 w-10 animate-spin rounded-full border-2 border-ink-400 border-t-ink-900" />
        </div>
      )}

      {snapshot && !loading && (
        <ScrollSection delay={100}>
          <p className="mb-4 font-mono text-xs text-ink-500">
            {snapshot.node_count} nodes · {snapshot.edge_count} edges ·{" "}
            <span className="text-ink-700">{snapshot.commit_sha.slice(0, 8)}</span>
          </p>
          <DependencyGraph snapshot={snapshot} height="620px" />
        </ScrollSection>
      )}
    </div>
  );
}
