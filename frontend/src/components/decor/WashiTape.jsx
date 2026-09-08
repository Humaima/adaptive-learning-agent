export default function WashiTape({ color = 'var(--gold)', top = -10, left = 32, rotate = -4 }) {
  return (
    <div style={{
      position: 'absolute', top, left, width: 64, height: 22, background: color,
      opacity: 0.85, transform: `rotate(${rotate}deg)`, borderRadius: 3,
    }} />
  )
}