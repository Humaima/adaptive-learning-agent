export default function MasteryRing({ value, size = 110, label }) {
  const radius = (size - 12) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference * (1 - value)

  return (
    <div style={{ textAlign: 'center' }}>
      <svg width={size} height={size}>
        <circle cx={size/2} cy={size/2} r={radius} stroke="var(--mint-soft)" strokeWidth="10" fill="none" />
        <circle
          cx={size/2} cy={size/2} r={radius} stroke="var(--mint)" strokeWidth="10" fill="none"
          strokeDasharray={circumference} strokeDashoffset={offset} strokeLinecap="round"
          transform={`rotate(-90 ${size/2} ${size/2})`}
        />
        <text x="50%" y="50%" textAnchor="middle" dy="0.35em" fontFamily="var(--font-display)" fontSize="22" fill="var(--ink)">
          {Math.round(value * 100)}%
        </text>
      </svg>
      {label && <div style={{ fontSize: '0.85rem', color: 'var(--ink-soft)', marginTop: 4 }}>{label}</div>}
    </div>
  )
}