import { Link } from 'react-router-dom'

const MOCK_PATH = [
  { name: 'Linear Algebra', minutes: 15, done: true },
  { name: 'Calculus', minutes: 20, done: false },
  { name: 'Neural Networks', minutes: 25, done: false },
]

export default function Dashboard() {
  return (
    <div className="paper-panel" style={{ padding: 32, marginTop: 24 }}>
      <div className="washi-tape" />
      <div className="pill-label">TODAY'S LEARNING PATH</div>
      <h2 style={{ marginTop: 12 }}>Your Adaptive Study Plan</h2>

      <div style={{ marginTop: 20 }}>
        {MOCK_PATH.map((step, i) => (
          <div key={step.name} style={{
            display: 'flex', alignItems: 'center', gap: 16, padding: '12px 0',
            borderBottom: i < MOCK_PATH.length - 1 ? '1px solid #EFEBE0' : 'none',
          }}>
            <div style={{
              width: 28, height: 28, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
              background: step.done ? 'var(--mint)' : 'var(--lavender-soft)', color: step.done ? 'white' : 'var(--ink)',
              fontWeight: 600, fontSize: '0.85rem',
            }}>{step.done ? '✓' : i + 1}</div>
            <div style={{ flex: 1 }}>{step.name}</div>
            <div style={{ color: 'var(--coral)', fontWeight: 600 }}>{step.minutes} min</div>
          </div>
        ))}
      </div>

      <Link to="/ask">
        <button className="btn-primary" style={{ marginTop: 24 }}>Ask Your Learning Agent</button>
      </Link>
    </div>
  )
}