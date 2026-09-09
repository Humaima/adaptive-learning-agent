import { useEffect, useState } from 'react'
import { getQuizHistory } from '../api/client.js'
import MasteryRing from '../components/MasteryRing.jsx'

export default function QuizHistory() {
  const [history, setHistory] = useState(null)

  useEffect(() => { getQuizHistory().then(setHistory) }, [])

  if (!history) return null

  const { entries, overall_accuracy } = history

  return (
    <div style={{ marginTop: 24 }}>
      <h2>Quiz Practice</h2>

      <div className="paper-panel" style={{ padding: 24, marginTop: 16, display: 'flex', alignItems: 'center', gap: 24 }}>
        <MasteryRing value={overall_accuracy} label="Overall accuracy" size={110} />
        <p style={{ color: 'var(--ink-soft)' }}>
          {entries.length === 0
            ? "You haven't answered any quiz questions yet — they'll show up here once you do."
            : `Based on your last ${entries.length} quiz answer${entries.length === 1 ? '' : 's'}.`}
        </p>
      </div>

      {entries.length > 0 && (
        <div style={{ display: 'grid', gap: 12, marginTop: 16 }}>
          {entries.map((e, i) => (
            <div key={i} className="paper-panel" style={{ padding: 16, display: 'flex', alignItems: 'center', gap: 16 }}>
              <div style={{
                width: 32, height: 32, borderRadius: '50%', flexShrink: 0,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                background: e.correct ? 'var(--mint-soft)' : 'var(--coral-soft)',
                color: e.correct ? 'var(--mint)' : 'var(--coral)', fontWeight: 700,
              }}>
                {e.correct ? '✓' : '✗'}
              </div>
              <div style={{ flex: 1 }}>
                <div className="pill-label">{e.concept_name}</div>
                <p style={{ marginTop: 4 }}>{e.question_snippet}</p>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--ink-soft)', whiteSpace: 'nowrap' }}>
                {new Date(e.timestamp).toLocaleDateString()}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
