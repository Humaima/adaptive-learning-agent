export default function ChatBubble({ role, children, onSave }) {
  return (
    <div className={`chat-bubble ${role}`}>
      {children}
      {onSave && <button className="save-note-btn" onClick={onSave}>💾 Save to Notes</button>}
    </div>
  )
}