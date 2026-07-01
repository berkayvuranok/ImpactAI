import type { ReactNode } from "react";

interface PageHeroProps {
  eyebrow: string;
  title: string;
  description?: string;
  children?: ReactNode;
}

export function PageHero({ eyebrow, title, description, children }: PageHeroProps) {
  return (
    <header className="relative overflow-hidden border-b border-ink-300 pb-16 pt-4 md:pb-24">
      <div className="absolute -right-20 top-0 h-64 w-64 rounded-full border border-ink-300/50 opacity-30" />
      <div className="absolute -left-10 bottom-0 h-40 w-40 rotate-45 border border-ink-300/30" />

      <p className="section-label animate-fade-up">{eyebrow}</p>
      <h1 className="display-title mt-4 max-w-4xl animate-fade-up">{title}</h1>
      {description && (
        <p className="mt-5 max-w-2xl text-lg leading-relaxed text-ink-600 animate-fade-up">
          {description}
        </p>
      )}
      {children && <div className="mt-8 animate-fade-up">{children}</div>}

      <div className="mt-12 overflow-hidden border-y border-ink-300 py-3">
        <div className="flex animate-marquee whitespace-nowrap">
          {[...Array(2)].map((_, copy) => (
            <div key={copy} className="flex shrink-0">
              {["GNN", "RISK FUSION", "DEP GRAPH", "SIMILARITY", "LLM XAI", "REVIEWERS"].map(
                (tag) => (
                  <span
                    key={`${copy}-${tag}`}
                    className="mx-8 font-mono text-xs uppercase tracking-[0.3em] text-ink-500"
                  >
                    {tag}
                  </span>
                ),
              )}
            </div>
          ))}
        </div>
      </div>
    </header>
  );
}
