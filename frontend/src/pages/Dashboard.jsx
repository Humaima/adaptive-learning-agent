import { useEffect, useState } from 'react'
import { getLearningPath, askAgent, answerQuiz } from '../api/client.js'
import NotebookSpread from '../components/NotebookSpread.jsx'
import WashiTape from '../components/decor/WashiTape.jsx'
import Ribbon from '../components/decor/Ribbon.jsx'
import StickyNote from '../components/decor/StickyNote.jsx'
import { StarDoodle, HeartDoodle } from '../components/decor/Doodle.jsx'
import ChatBubble from '../components/ChatBubble.jsx'
import QuizCard from '../components/QuizCard.jsx'
import '../components/ChatBubble.css'
import '../components/QuizCard.css'
import '../components/NotebookSpread.css'

const FOLLOW_UPS = ['Can you show me another example?', 'Why does that work?', 'Quiz me on this']

export default function Dashboard() {
  const [path, setPath] = useState(null)
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState([])
  const [activeQuiz, setActiveQuiz] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => { getLearningPath().then(setPath) }, [])

  const pushTeachingSteps = (result) => {
    const steps = (result.teaching_history || []).map(s => ({
      role: 'agent',
      text: `${s.transition_note ? s.transition_note + '\n\n' : ''}${s.explanation}`,
    }))
    setMessages(prev => [...prev, ...steps])
  }

  const send = async (text) => {
    if (!text.trim()) return
    setMessages(prev => [...prev, { role: 'student', text }])
    setLoading(true)
    try {
      const result = await askAgent(text)
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
    } finally { setLoading(false) }
  }

  const leftPage = (
    <>
      <Ribbon />
      <StarDoodle style={{ top: 16, right: 24 }} />
      <div className="pill-label" style={{ marginTop: 12 }}>TODAY'S LEARNING PATH</div>
      <h2 style={{ marginTop: 12 }}>Your Adaptive Study Plan</h2>

      <div style={{ marginTop: 20 }}>
        {path?.map((step, i) => (
          <div key={step.concept_id} style={{
            display: 'flex', alignItems: 'center', gap: 16, padding: '12px 0',
            borderBottom: i < path.length - 1 ? '1px solid #EFEBE0' : 'none',
          }}>
            <div style={{
              width: 28, height: 28, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
              background: 'var(--lavender-soft)', fontWeight: 600, fontSize: '0.85rem',
            }}>{i + 1}</div>
            <div style={{ flex: 1 }}>
              {step.concept_name}
              <div style={{ fontSize: '0.75rem', color: 'var(--ink-soft)' }}>{step.domain}</div>
            </div>
            <div style={{ color: 'var(--coral)', fontWeight: 600 }}>{step.estimated_minutes} min</div>
          </div>
        ))}
      </div>

      <StickyNote color="var(--gold)" rotate={-4} style={{ position: 'absolute', bottom: 28, left: 36 }}>
        You've got this! 🌟
      </StickyNote>
    </>
  )

  const rightPage = (
    <>
      <WashiTape />
      <HeartDoodle style={{ top: 16, right: 28 }} />
      <div className="pill-label" style={{ marginTop: 12 }}>ASK YOUR LEARNING AGENT</div>
      <h2 style={{ marginTop: 12, marginBottom: 16 }}>What are you working on?</h2>

      <div style={{ minHeight: 220, maxHeight: 340, overflowY: 'auto' }}>
        {messages.map((m, i) => <ChatBubble key={i} role={m.role}>{m.text}</ChatBubble>)}
        {activeQuiz && <QuizCard quiz={activeQuiz} onSubmit={handleQuizSubmit} submitting={loading} />}
      </div>

      {!activeQuiz && messages.length > 0 && (
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', margin: '12px 0' }}>
          {FOLLOW_UPS.map(fu => (
            <button key={fu} className="follow-up-chip" onClick={() => send(fu)}>{fu}</button>
          ))}
        </div>
      )}

      {!activeQuiz && (
        <div style={{ display: 'flex', gap: 12, marginTop: 12 }}>
          <input
            style={{ flex: 1, padding: '12px 18px', borderRadius: 999, border: '1px solid #E4E0F5' }}
            placeholder="Ask anything about your studies..."
            value={question}
            onChange={e => setQuestion(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && send(question)}
          />
          <button className="btn-primary" onClick={() => send(question)} disabled={loading}>Ask</button>
        </div>
      )}
      <p style={{ fontSize: '0.7rem', color: 'var(--ink-soft)', marginTop: 8 }}>
        AI responses can make mistakes. Always review important info.
      </p>
    </>
  )

  return <NotebookSpread leftPage={leftPage} rightPage={rightPage} />
}