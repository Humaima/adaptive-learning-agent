import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { login } from '../api/client.js'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      await login(username, password)
      navigate('/')
    } catch {
      setError('Incorrect username or password.')
    }
  }

  return (
    <div className="paper-panel" style={{ maxWidth: 380, margin: '60px auto', padding: 32 }}>
      <h2>Welcome back</h2>
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 16 }}>
        <input placeholder="Username" value={username} onChange={e => setUsername(e.target.value)} />
        <input type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} />
        {error && <p style={{ color: 'var(--coral)' }}>{error}</p>}
        <button className="btn-primary" type="submit">Log In</button>
      </form>
      <p style={{ marginTop: 16 }}>No account? <Link to="/register">Register</Link></p>
    </div>
  )
}