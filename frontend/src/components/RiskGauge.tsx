interface RiskGaugeProps {
  score: number;
  label?: string;
}

function riskColor(score: number): string {
  if (score >= 75) return "#ef4444";
  if (score >= 50) return "#f97316";
  if (score >= 25) return "#eab308";
  return "#22c55e";
}

export function RiskGauge({ score, label = "Risk Score" }: RiskGaugeProps) {
  const clamped = Math.min(Math.max(score, 0), 100);
  const color = riskColor(clamped);
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (clamped / 100) * circumference;

  return (
    <div className="flex flex-col items-center gap-2">
      <svg width="140" height="140" viewBox="0 0 140 140">
        <circle cx="70" cy="70" r={radius} fill="none" stroke="#1e293b" strokeWidth="10" />
        <circle
          cx="70"
          cy="70"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform="rotate(-90 70 70)"
        />
        <text x="70" y="68" textAnchor="middle" fill="white" fontSize="24" fontWeight="600">
          {clamped.toFixed(0)}
        </text>
        <text x="70" y="88" textAnchor="middle" fill="#94a3b8" fontSize="11">
          / 100
        </text>
      </svg>
      <p className="text-sm font-medium text-slate-300">{label}</p>
    </div>
  );
}
