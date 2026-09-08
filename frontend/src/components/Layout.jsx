import NavBar from './NavBar.jsx'

export default function Layout({ children }) {
  return (
    <div>
      <NavBar />
      <main style={{ maxWidth: 1100, margin: '0 auto', padding: '0 24px 48px' }}>
        {children}
      </main>
    </div>
  )
}