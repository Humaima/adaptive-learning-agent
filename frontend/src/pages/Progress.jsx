import { useEffect, useState } from 'react'
import { getMastery } from '../api/client.js'
import MasteryRing from '../components/MasteryRing.jsx'

export default function Progress() {
  const [mastery, setMastery] = useState([])

  useEffect(() => { getMastery().then(data => setMastery(data.mastery)) }, [])

  const byDomain = mastery.reduce((acc, m) => {
    acc[m.domain] = acc[m.domain] || []
    acc[m.domain].push(m)
    return acc
  }, {})

  return (
    <div style={{ marginTop: 24 }}>
      <h2>Your Concept Mastery</h2>
      {Object.entries(byDomain).map(([domain, concepts]) => (
        <div key={domain} className="paper-panel" style={{ padding: 24, marginTop: 16 }}>
          <h3>{domain}</h3>
          <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap', marginTop: 12 }}>
            {concepts.map(c => (
              <MasteryRing key={c.concept_id} value={c.mastery ?? 0} label={c.concept_name} size={90} />
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}