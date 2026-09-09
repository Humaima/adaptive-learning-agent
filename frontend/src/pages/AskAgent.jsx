import { useState } from 'react'
import { askAgent, answerQuiz, addNote } from '../api/client.js'
import ChatBubble from '../components/ChatBubble.jsx'
import QuizCard from '../components/QuizCard.jsx'
import '../components/ChatBubble.css'
import '../components/QuizCard.css'

export default function AskAgent() {
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState([]) // {role, text}
  const [activeQuiz, setActiveQuiz] = useState(null)
  const [loading, setLoading] = useState(false)

  const pushTeachingSteps = (turnResponse) => {
    const steps = turnResponse.teaching_history || []
    const newBubbles = steps.map(step => ({
      role: 'agent',
      concept_id: step.concept_id,
      concept_name: step.concept_name,
      text: `${step.transition_note ? step.transition_note + '\n\n' : ''}${step.explanation}\n\nWorked example: ${step.worked_example}`,
    }))
    setMessages(prev => [...prev, ...newBubbles])
  }

  const handleAsk = async () => {
    if (!question.trim()) return
    setMessages(prev => [...prev, { role: 'student', text: question }])
    setLoading(true)
    try {
      const result = await askAgent(question)
      pushTeachingSteps(result)
      setActiveQuiz(result.status === 'awaiting_answers' ? result.quiz : null)
    } finally {
      setLoading(false)
      setQuestion('')
    }
  }

  const handleQuizSubmit = async (answers) => {
    setLoading(true)
    try {
      const result = await answerQuiz(answers)
      pushTeachingSteps(result)
      setActiveQuiz(result.status === 'awaiting_answers' ? result.quiz : null)
      if (result.status === 'done') {
        setMessages(prev => [...prev, { role: 'agent', text: "You've got this concept down! Ask me anything else." }])
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="paper-panel" style={{ padding: 32, marginTop: 24 }}>
      <div className="pill-label">ASK YOUR LEARNING AGENT</div>
      <h2 style={{ marginTop: 12, marginBottom: 20 }}>What are you working on?</h2>

      <div style={{ minHeight: 200 }}>
        {messages.map((m, i) => (
          <ChatBubble
            key={i} role={m.role}
            onSave={m.role === 'agent' ? () => addNote(m.concept_id, m.concept_name, m.text) : null}
          >
            {m.text}
          </ChatBubble>
        ))}
        {activeQuiz && <QuizCard quiz={activeQuiz} onSubmit={handleQuizSubmit} submitting={loading} />}
      </div>

      {!activeQuiz && (
        <div style={{ display: 'flex', gap: 12, marginTop: 20 }}>
          <input
            style={{ flex: 1, padding: '12px 18px', borderRadius: 999, border: '1px solid #E4E0F5' }}
            placeholder="Ask anything about your studies..."
            value={question}
            onChange={e => setQuestion(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleAsk()}
          />
          <button className="btn-primary" onClick={handleAsk} disabled={loading}>
            {loading ? '…' : 'Ask'}
          </button>
        </div>
      )}
    </div>
  )
}