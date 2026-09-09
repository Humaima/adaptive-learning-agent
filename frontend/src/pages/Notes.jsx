import { useEffect, useState } from 'react'
import { getNotes, deleteNote } from '../api/client.js'

export default function Notes() {
  const [notes, setNotes] = useState([])
  const load = () => getNotes().then(setNotes)
  useEffect(() => { load() }, [])

  return (
    <div style={{ marginTop: 24 }}>
      <h2>Your Notes</h2>
      {notes.length === 0 && <p style={{ color: 'var(--ink-soft)' }}>No notes yet — save an explanation from Ask Agent to get started.</p>}
      <div style={{ display: 'grid', gap: 16, marginTop: 16 }}>
        {notes.map(n => (
          <div key={n.id} className="paper-panel" style={{ padding: 20 }}>
            <div className="pill-label">{n.concept_id}</div>
            <h3 style={{ marginTop: 8 }}>{n.title}</h3>
            <p style={{ whiteSpace: 'pre-wrap', color: 'var(--ink-soft)' }}>{n.content}</p>
            <button onClick={() => deleteNote(n.id).then(load)} style={{ background: 'none', border: 'none', color: 'var(--coral)', cursor: 'pointer' }}>
              Delete
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}