import { useEffect, useState } from 'react'
import { getDueFlashcards, reviewFlashcard, generateFlashcards, getConcepts } from '../api/client.js'
import './Flashcards.css'

export default function Flashcards() {
  const [cards, setCards] = useState([])
  const [index, setIndex] = useState(0)
  const [flipped, setFlipped] = useState(false)
  const [concepts, setConcepts] = useState([])
  const [selectedConcept, setSelectedConcept] = useState('')

  const loadDue = () => getDueFlashcards().then(c => { setCards(c); setIndex(0); setFlipped(false) })
  useEffect(() => { loadDue(); getConcepts().then(setConcepts) }, [])

  const handleGenerate = async () => {
    if (!selectedConcept) return
    await generateFlashcards(selectedConcept)
    loadDue()
  }

  const handleReview = async (knewIt) => {
    await reviewFlashcard(cards[index].id, knewIt)
    if (index + 1 < cards.length) { setIndex(index + 1); setFlipped(false) } else loadDue()
  }

  return (
    <div style={{ marginTop: 24 }}>
      <h2>Flashcards</h2>

      <div className="paper-panel" style={{ padding: 20, marginBottom: 20, display: 'flex', gap: 12, alignItems: 'center' }}>
        <select value={selectedConcept} onChange={e => setSelectedConcept(e.target.value)}>
          <option value="">Choose a concept to generate cards for...</option>
          {concepts.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <button className="btn-primary" onClick={handleGenerate}>Generate Flashcards</button>
      </div>

      {cards.length === 0 && <p style={{ color: 'var(--ink-soft)' }}>No cards due for review right now. 🎉</p>}

      {cards.length > 0 && (
        <>
          <div className="paper-panel flashcard" onClick={() => setFlipped(f => !f)}>
            <div className="pill-label">{cards[index].concept_id}</div>
            <p style={{ fontSize: '1.2rem', marginTop: 20, textAlign: 'center' }}>
              {flipped ? cards[index].back : cards[index].front}
            </p>
            {!flipped && <p style={{ textAlign: 'center', color: 'var(--ink-soft)', fontSize: '0.8rem' }}>(tap to reveal answer)</p>}
          </div>
          {flipped && (
            <div style={{ display: 'flex', gap: 12, justifyContent: 'center', marginTop: 16 }}>
              <button className="btn-secondary" onClick={() => handleReview(false)}>😕 Still learning</button>
              <button className="btn-primary" onClick={() => handleReview(true)}>✅ I knew it</button>
            </div>
          )}
        </>
      )}
    </div>
  )
}