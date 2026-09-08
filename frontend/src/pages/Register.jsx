import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { register } from '../api/client.js'

export default function Register() {
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      await register(username, email, password)
      navigate('/')
    } catch (err) {
      // FastAPI's own errors use {detail: "..."}; slowapi's rate-limit handler
      // uses a differently-shaped {error: "..."} — check both rather than
      // showing one hardcoded guess for every possible failure.
      const message = err.response?.data?.detail || err.response?.data?.error
      setError(message || 'Something went wrong. Please try again.')
    }
  }

  return (
    <div className="paper-panel" style={{ maxWidth: 380, margin: '60px auto', padding: 32 }}>
      <h2>Create your account</h2>
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 16 }}>
        <input placeholder="Username" value={username} onChange={e => setUsername(e.target.value)} />
        <input placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} />
        <input type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} />
        {error && <p style={{ color: 'var(--coral)' }}>{error}</p>}
        <button className="btn-primary" type="submit">Register</button>
      </form>
      <p style={{ marginTop: 16 }}>Already have an account? <Link to="/login">Log in</Link></p>
    </div>
  )
}