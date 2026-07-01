import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "../api/client";
import type { Repository, RiskSummary } from "../api/types";

export function DashboardPage() {
  const [repos, setRepos] = useState<Repository[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [risk, setRisk] = useState<RiskSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [creating, setCreating] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const list = await api.listRepositories();
      setRepos(list.items);
      if (list.items.length && !selectedId) {
        setSelectedId(list.items[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load repositories");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    api
      .getRiskSummary(selectedId)
      .then(setRisk)
      .catch(() => setRisk(null));
  }, [selectedId]);

  const handleCreate = async (event: FormEvent) => {
    event.preventDefault();
    setCreating(true);
    try {
      await api.createRepository({ name, url });
      setName("");
      setUrl("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create repository");
    } finally {
      setCreating(false);
    }
  };

  const handleSync = async (id: string) => {
    await api.syncRepository(id);
    await load();
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this repository?")) return;
    await api.deleteRepository(id);
    if (selectedId === id) setSelectedId(null);
    await load();
  };

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-semibold text-white">Dashboard</h2>
        <p className="mt-1 text-slate-400">Manage repositories and monitor prediction risk.</p>
      </div>

      {error && (
        <div className="rounded-lg border border-red-900/50 bg-red-950/30 px-4 py-3 text-sm text-red-300">
          {error}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
          <h3 className="font-medium text-white">Add repository</h3>
          <form onSubmit={handleCreate} className="mt-4 space-y-3">
            <input
              placeholder="Name"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white"
            />
            <input
              placeholder="https://github.com/org/repo"
              required
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white"
            />
            <button
              type="submit"
              disabled={creating}
              className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-500 disabled:opacity-50"
            >
              {creating ? "Adding…" : "Add repository"}
            </button>
          </form>
        </section>

        <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
          <h3 className="font-medium text-white">Risk overview</h3>
          {risk ? (
            <div className="mt-4 space-y-4">
              <div className="grid grid-cols-3 gap-4 text-center">
                <Stat label="Avg risk" value={risk.average_risk_score.toFixed(1)} />
                <Stat label="High risk" value={String(risk.high_risk_predictions)} />
                <Stat label="Total" value={String(risk.total_predictions)} />
              </div>
              {risk.trend.length > 0 && (
                <div className="h-40">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={risk.trend}>
                      <CartesianGrid stroke="#334155" strokeDasharray="3 3" />
                      <XAxis dataKey="created_at" hide />
                      <YAxis domain={[0, 100]} stroke="#64748b" fontSize={11} />
                      <Tooltip
                        contentStyle={{ background: "#0f172a", border: "1px solid #334155" }}
                      />
                      <Line type="monotone" dataKey="risk_score" stroke="#22d3ee" dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          ) : (
            <p className="mt-4 text-sm text-slate-500">Select a repository with predictions.</p>
          )}
        </section>
      </div>

      <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
        <h3 className="font-medium text-white">Repositories</h3>
        {loading ? (
          <p className="mt-4 text-sm text-slate-500">Loading…</p>
        ) : repos.length === 0 ? (
          <p className="mt-4 text-sm text-slate-500">No repositories yet.</p>
        ) : (
          <div className="mt-4 divide-y divide-slate-800">
            {repos.map((repo) => (
              <div
                key={repo.id}
                className={`flex flex-wrap items-center justify-between gap-4 py-4 ${
                  selectedId === repo.id ? "bg-brand-500/5" : ""
                }`}
              >
                <button
                  type="button"
                  onClick={() => setSelectedId(repo.id)}
                  className="text-left"
                >
                  <p className="font-medium text-white">{repo.name}</p>
                  <p className="font-mono text-xs text-slate-500">{repo.url}</p>
                </button>
                <div className="flex flex-wrap gap-2">
                  <Link
                    to={`/predict?repo=${repo.id}`}
                    className="rounded-lg border border-slate-700 px-3 py-1.5 text-xs text-slate-300 hover:border-brand-500"
                  >
                    Predict
                  </Link>
                  <Link
                    to={`/graph?repo=${repo.id}`}
                    className="rounded-lg border border-slate-700 px-3 py-1.5 text-xs text-slate-300 hover:border-brand-500"
                  >
                    Graph
                  </Link>
                  <button
                    type="button"
                    onClick={() => handleSync(repo.id)}
                    className="rounded-lg border border-slate-700 px-3 py-1.5 text-xs text-slate-300 hover:border-brand-500"
                  >
                    Sync
                  </button>
                  <button
                    type="button"
                    onClick={() => handleDelete(repo.id)}
                    className="rounded-lg border border-red-900/50 px-3 py-1.5 text-xs text-red-400 hover:border-red-500"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-slate-950/60 py-3">
      <p className="text-2xl font-semibold text-brand-400">{value}</p>
      <p className="text-xs text-slate-500">{label}</p>
    </div>
  );
}
