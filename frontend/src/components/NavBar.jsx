import { NavLink } from 'react-router-dom'
import './NavBar.css'

export default function NavBar() {
  return (
    <nav className="navbar">
      <div className="navbar-brand">📖 StudyNook</div>
      <div className="navbar-links">
        <NavLink to="/" end className={({ isActive }) => isActive ? 'active' : ''}>Home</NavLink>
        <NavLink to="/ask" className={({ isActive }) => isActive ? 'active' : ''}>Ask Agent</NavLink>
        <NavLink to="/progress" className={({ isActive }) => isActive ? 'active' : ''}>Progress</NavLink>
      </div>
      <div className="navbar-streak">🔥 <span>12</span></div>
    </nav>
  )
}