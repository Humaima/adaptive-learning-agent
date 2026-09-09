import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import Dashboard from './pages/Dashboard.jsx'
import AskAgent from './pages/AskAgent.jsx'
import Progress from './pages/Progress.jsx'
import Notes from './pages/Notes.jsx'
import Login from './pages/Login.jsx'
import Register from './pages/Register.jsx'
import { isLoggedIn } from './api/client.js'

function ProtectedRoute({ children }) {
  return isLoggedIn() ? children : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/*" element={
          <ProtectedRoute>
            <Layout>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/ask" element={<AskAgent />} />
                <Route path="/progress" element={<Progress />} />
                <Route path="/notes" element={<Notes />} />
              </Routes>
            </Layout>
          </ProtectedRoute>
        } />
      </Routes>
    </BrowserRouter>
  )
}