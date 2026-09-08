export default function MiniWidgetRow() {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginTop: 20 }}>
      <div className="mini-widget">
        <div className="mini-widget-title">New note <span>See all</span></div>
        <div className="mini-widget-line">📄 Calculus Derivatives</div>
        <div className="mini-widget-line">📄 Newton's Laws</div>
      </div>
      <div className="mini-widget">
        <div className="mini-widget-title">Flashcards <span>See all</span></div>
        <div style={{ fontSize: '1.6rem', fontFamily: 'var(--font-display)' }}>48</div>
        <div style={{ fontSize: '0.75rem', color: 'var(--ink-soft)' }}>cards due for review</div>
      </div>
      <div className="mini-widget">
        <div className="mini-widget-title">Quiz Practice <span>See all</span></div>
        <div style={{ fontSize: '1.6rem', fontFamily: 'var(--font-display)', color: 'var(--coral)' }}>85%</div>
      </div>
      <div className="mini-widget">
        <div className="mini-widget-title">Weekly Schedule</div>
        <div style={{ display: 'flex', gap: 6, marginTop: 6 }}>
          {['M','T','W','T','F'].map((d, i) => (
            <div key={i} style={{
              width: 22, height: 22, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '0.65rem', background: i === 1 ? 'var(--coral)' : 'var(--mint-soft)',
              color: i === 1 ? 'white' : 'var(--ink)',
            }}>{d}</div>
          ))}
        </div>
      </div>
    </div>
  )
}

