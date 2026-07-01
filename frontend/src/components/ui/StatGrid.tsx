interface StatItem {
  label: string;
  value: string;
}

export function StatGrid({ items }: { items: StatItem[] }) {
  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
      {items.map((item) => (
        <div key={item.label} className="panel panel-hover p-6">
          <p className="font-heading text-3xl font-bold text-ink-900 md:text-4xl">{item.value}</p>
          <p className="mt-2 font-mono text-[11px] uppercase tracking-widest text-ink-500">
            {item.label}
          </p>
        </div>
      ))}
    </div>
  );
}
