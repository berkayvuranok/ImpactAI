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
import { PageHero } from "../components/ui/PageHero";
import { ScrollSection } from "../components/ui/ScrollSection";
import { Slider } from "../components/ui/Slider";
import { StatGrid } from "../components/ui/StatGrid";

const FEATURES = [
  {
    title: "GNN Impact",
    desc: "Graph neural network propagates change signals through your dependency graph.",
  },
  {
    title: "Risk Fusion",
    desc: "Ensemble of classical ML + GNN scores for calibrated regression probability.",
  },
  {
    title: "Similarity Search",
    desc: "Qdrant retrieves historically risky commits similar to your diff.",
  },
  {
    title: "Smart Reviewers",
    desc: "Ownership and expertise scoring suggests the best reviewers automatically.",
  },
];

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
      if (list.items.length && !selectedId) setSelectedId(list.items[0].id);
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
    api.getRiskSummary(selectedId).then(setRisk).catch(() => setRisk(null));
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

  const stats = risk
    ? [
        { label: "Avg Risk", value: risk.average_risk_score.toFixed(1) },
        { label: "High Risk", value: String(risk.high_risk_predictions) },
        { label: "Total Runs", value: String(risk.total_predictions) },
        { label: "Repos", value: String(repos.length) },
      ]
    : [
        { label: "Repos", value: String(repos.length) },
        { label: "Avg Risk", value: "—" },
        { label: "High Risk", value: "—" },
        { label: "Total Runs", value: "—" },
      ];

  return (
    <div>
      <PageHero
        eyebrow="Control Center"
        title="Predict code impact before it ships."
        description="Monitor repositories, track regression risk, and launch predictions from a single monochrome command deck."
      >
        <div className="flex flex-wrap gap-3">
          <Link to="/predict" className="btn-primary">
            Run Prediction →
          </Link>
          <Link to="/graph" className="btn-ghost">
            Explore Graph
          </Link>
        </div>
      </PageHero>

      {error && (
        <div className="mb-8 rounded-xl border border-ink-400 bg-ink-100 px-4 py-3 font-mono text-sm text-ink-700">
          {error}
        </div>
      )}

      <ScrollSection delay={0}>
        <StatGrid items={stats} />
      </ScrollSection>

      <ScrollSection delay={100}>
        <Slider title="Your Repositories" subtitle="Slide 01 — Repos" itemWidth="min(88vw, 340px)">
          {loading ? (
            <div className="panel flex h-48 items-center justify-center">
              <span className="font-mono text-sm text-ink-500">Loading…</span>
            </div>
          ) : repos.length === 0 ? (
            <div className="panel flex h-48 flex-col items-center justify-center gap-3 p-8 text-center">
              <p className="font-heading text-lg text-ink-700">No repositories yet</p>
              <p className="font-mono text-xs text-ink-500">Add one below to get started</p>
            </div>
          ) : (
            repos.map((repo) => (
              <article
                key={repo.id}
                className={`panel panel-hover flex h-48 cursor-pointer flex-col justify-between p-6 ${
                  selectedId === repo.id ? "border-ink-700 ring-1 ring-ink-700" : ""
                }`}
                onClick={() => setSelectedId(repo.id)}
                onKeyDown={(e) => e.key === "Enter" && setSelectedId(repo.id)}
                role="button"
                tabIndex={0}
              >
                <div>
                  <p className="font-mono text-[10px] uppercase tracking-widest text-ink-500">
                    {repo.provider}
                  </p>
                  <h4 className="mt-2 font-heading text-xl font-semibold text-ink-900">{repo.name}</h4>
                  <p className="mt-2 truncate font-mono text-[11px] text-ink-500">{repo.url}</p>
                </div>
                <div className="flex flex-wrap gap-2" onClick={(e) => e.stopPropagation()}>
                  <Link to={`/predict?repo=${repo.id}`} className="btn-ghost !px-3 !py-1 !text-[11px]">
                    Predict
                  </Link>
                  <Link to={`/graph?repo=${repo.id}`} className="btn-ghost !px-3 !py-1 !text-[11px]">
                    Graph
                  </Link>
                  <button
                    type="button"
                    onClick={() => handleSync(repo.id)}
                    className="btn-ghost !px-3 !py-1 !text-[11px]"
                  >
                    Sync
                  </button>
                  <button
                    type="button"
                    onClick={() => handleDelete(repo.id)}
                    className="rounded-full border border-ink-400 px-3 py-1 text-[11px] text-ink-500 transition hover:border-ink-600 hover:text-ink-800"
                  >
                    Delete
                  </button>
                </div>
              </article>
            ))
          )}
        </Slider>
      </ScrollSection>

      <ScrollSection delay={150}>
        <Slider title="Platform Capabilities" subtitle="Slide 02 — Features" itemWidth="min(88vw, 300px)">
          {FEATURES.map((f) => (
            <article key={f.title} className="panel panel-hover flex h-56 flex-col justify-between p-6">
              <p className="font-mono text-[10px] uppercase tracking-widest text-ink-500">{f.title}</p>
              <p className="font-heading text-lg leading-snug text-ink-800">{f.desc}</p>
              <div className="h-px w-12 bg-ink-400" />
            </article>
          ))}
        </Slider>
      </ScrollSection>

      <ScrollSection delay={200}>
        <div className="grid gap-8 lg:grid-cols-2">
          <section className="panel p-8">
            <p className="section-label">Add Repository</p>
            <h3 className="mt-2 font-heading text-2xl font-semibold text-ink-900">Connect a repo</h3>
            <form onSubmit={handleCreate} className="mt-6 space-y-4">
              <input
                placeholder="Repository name"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="input-field"
              />
              <input
                placeholder="https://github.com/org/repo"
                required
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="input-field"
              />
              <button type="submit" disabled={creating} className="btn-primary w-full sm:w-auto">
                {creating ? "Adding…" : "Add repository"}
              </button>
            </form>
          </section>

          <section className="panel p-8">
            <p className="section-label">Risk Trend</p>
            <h3 className="mt-2 font-heading text-2xl font-semibold text-ink-900">Score history</h3>
            {risk && risk.trend.length > 0 ? (
              <div className="mt-6 h-52">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={risk.trend}>
                    <CartesianGrid stroke="#262626" strokeDasharray="4 4" vertical={false} />
                    <XAxis dataKey="created_at" hide />
                    <YAxis domain={[0, 100]} stroke="#525252" fontSize={10} tickLine={false} />
                    <Tooltip
                      contentStyle={{
                        background: "#111",
                        border: "1px solid #404040",
                        borderRadius: 12,
                        fontFamily: "IBM Plex Mono",
                        fontSize: 11,
                      }}
                      labelStyle={{ color: "#737373" }}
                      itemStyle={{ color: "#fff" }}
                    />
                    <Line
                      type="monotone"
                      dataKey="risk_score"
                      stroke="#ffffff"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <p className="mt-8 font-mono text-sm text-ink-500">
                Select a repo with predictions to see the trend line.
              </p>
            )}
          </section>
        </div>
      </ScrollSection>
    </div>
  );
}
