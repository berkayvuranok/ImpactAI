interface RiskGaugeProps {
  score: number;
  label?: string;
}

function strokeForScore(score: number): string {
  if (score >= 75) return "#ffffff";
  if (score >= 50) return "#d4d4d4";
  if (score >= 25) return "#737373";
  return "#404040";
}

export function RiskGauge({ score, label = "Risk Score" }: RiskGaugeProps) {
  const clamped = Math.min(Math.max(score, 0), 100);
  const stroke = strokeForScore(clamped);
  const radius = 58;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (clamped / 100) * circumference;

  return (
    <div className="flex flex-col items-center gap-3">
      <div className="relative">
        <svg width="160" height="160" viewBox="0 0 160 160">
          <circle cx="80" cy="80" r={radius} fill="none" stroke="#262626" strokeWidth="3" />
          <circle
            cx="80"
            cy="80"
            r={radius}
            fill="none"
            stroke={stroke}
            strokeWidth="3"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            transform="rotate(-90 80 80)"
            className="transition-all duration-700"
          />
          <text
            x="80"
            y="76"
            textAnchor="middle"
            fill="#fafafa"
            fontSize="32"
            fontWeight="700"
            fontFamily="Syne, sans-serif"
          >
            {clamped.toFixed(0)}
          </text>
          <text x="80" y="98" textAnchor="middle" fill="#737373" fontSize="11" fontFamily="IBM Plex Mono">
            / 100
          </text>
        </svg>
      </div>
      <p className="font-mono text-[11px] uppercase tracking-widest text-ink-500">{label}</p>
    </div>
  );
}
