export default function StickyNote({ children, color = 'var(--gold)', rotate = -3, style = {} }) {
  return (
    <div style={{
      background: color, padding: '14px 16px', borderRadius: 4, transform: `rotate(${rotate}deg)`,
      boxShadow: '2px 4px 10px rgba(0,0,0,0.12)', fontFamily: 'var(--font-body)', fontSize: '0.85rem',
      maxWidth: 160, ...style,
    }}>
      {children}
    </div>
  )
}