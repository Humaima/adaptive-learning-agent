import { NavLink, useNavigate } from 'react-router-dom'
import { logout } from '../api/client.js'
import './NavBar.css'

export default function NavBar() {
  const navigate = useNavigate()
  return (
    <nav className="navbar">
      <div className="navbar-brand">📖 StudyNook</div>
      <div className="navbar-links">
        <NavLink to="/" end className={({ isActive }) => isActive ? 'active' : ''}>Home</NavLink>
        <NavLink to="/ask" className={({ isActive }) => isActive ? 'active' : ''}>Ask Agent</NavLink>
        <NavLink to="/progress" className={({ isActive }) => isActive ? 'active' : ''}>Progress</NavLink>
        <NavLink to="/notes" className={({ isActive }) => isActive ? 'active' : ''}>Notes</NavLink>
        <NavLink to="/flashcards" className={({ isActive }) => isActive ? 'active' : ''}>Flashcards</NavLink>
      </div>
      <button onClick={() => { logout(); navigate('/login') }} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--ink-soft)' }}>
        Log out
      </button>
    </nav>
  )
}