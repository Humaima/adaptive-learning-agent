import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getLearningPath } from '../api/client.js'

export default function Dashboard() {
  const [path, setPath] = useState(null)

  useEffect(() => { getLearningPath().then(setPath) }, [])

  return (
    <div className="paper-panel" style={{ padding: 32, marginTop: 24 }}>
      <div className="washi-tape" />
      <div className="pill-label">TODAY'S LEARNING PATH</div>
      <h2 style={{ marginTop: 12 }}>Your Adaptive Study Plan</h2>

      {path === null && <p style={{ marginTop: 20, color: 'var(--ink-soft)' }}>Loading your path…</p>}

      {path?.length === 0 && (
        <p style={{ marginTop: 20, color: 'var(--ink-soft)' }}>
          Nothing new to recommend yet — ask your agent a question to get started!
        </p>
      )}

      <div style={{ marginTop: 20 }}>
        {path?.map((step, i) => (
          <div key={step.concept_id} style={{
            display: 'flex', alignItems: 'center', gap: 16, padding: '12px 0',
            borderBottom: i < path.length - 1 ? '1px solid #EFEBE0' : 'none',
          }}>
            <div style={{
              width: 28, height: 28, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
              background: 'var(--lavender-soft)', color: 'var(--ink)', fontWeight: 600, fontSize: '0.85rem',
            }}>{i + 1}</div>
            <div style={{ flex: 1 }}>
              {step.concept_name}
              <div style={{ fontSize: '0.75rem', color: 'var(--ink-soft)' }}>{step.domain}</div>
            </div>
            <div style={{ color: 'var(--coral)', fontWeight: 600 }}>{step.estimated_minutes} min</div>
          </div>
        ))}
      </div>

      <Link to="/ask">
        <button className="btn-primary" style={{ marginTop: 24 }}>Ask Your Learning Agent</button>
      </Link>
    </div>
  )
}