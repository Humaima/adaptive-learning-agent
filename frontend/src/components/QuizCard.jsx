import { useState } from 'react'

export default function QuizCard({ quiz, onSubmit, submitting }) {
  const [answers, setAnswers] = useState({})

  const setAnswer = (questionId, value) => setAnswers(prev => ({ ...prev, [questionId]: value }))
  const allAnswered = quiz.questions.every(q => answers[q.question_id]?.trim())

  return (
    <div className="quiz-card">
      <div className="washi-tape" />
      <div className="pill-label">QUICK CHECK · {quiz.difficulty.toUpperCase()}</div>
      <h3 style={{ marginTop: 12 }}>Let's see if that made sense</h3>

      {quiz.questions.map((q, i) => (
        <div key={q.question_id} className="quiz-question">
          <p><strong>{i + 1}.</strong> {q.question_text}</p>
          {q.question_type === 'mcq' ? (
            <div className="quiz-options">
              {q.options.map(opt => (
                <button
                  key={opt.label}
                  className={`quiz-option ${answers[q.question_id] === opt.label ? 'selected' : ''}`}
                  onClick={() => setAnswer(q.question_id, opt.label)}
                >
                  <span className="quiz-option-label">{opt.label}</span> {opt.text}
                </button>
              ))}
            </div>
          ) : (
            <textarea
              className="quiz-textarea"
              placeholder="Type your answer..."
              value={answers[q.question_id] || ''}
              onChange={e => setAnswer(q.question_id, e.target.value)}
            />
          )}
        </div>
      ))}

      <button className="btn-primary" disabled={!allAnswered || submitting} onClick={() => onSubmit(answers)}>
        {submitting ? 'Checking…' : 'Submit Answers'}
      </button>
    </div>
  )
}