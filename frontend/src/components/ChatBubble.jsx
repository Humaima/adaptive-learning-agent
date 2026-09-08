export default function ChatBubble({ role, children }) {
  return <div className={`chat-bubble ${role}`}>{children}</div>
}

