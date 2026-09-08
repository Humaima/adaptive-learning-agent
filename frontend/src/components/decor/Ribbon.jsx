export default function Ribbon({ color = 'var(--coral)' }) {
  return (
    <svg width="36" height="52" style={{ position: 'absolute', top: -8, left: 24 }}>
      <path d="M0 0 H36 V44 L18 34 L0 44 Z" fill={color} />
    </svg>
  )
}