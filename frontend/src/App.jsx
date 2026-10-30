import { useEffect, useState } from 'react'
import './App.css'

const API_URL = 'http://127.0.0.1:8000'

function App() {
  const [status, setStatus] = useState('se verifică...')
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch(API_URL + '/health')
      .then((response) => {
        if (!response.ok) {
          throw new Error('Răspuns invalid de la server: ' + response.status)
        }
        return response.json()
      })
      .then((data) => setStatus(data.status))
      .catch((err) => setError(err.message))
  }, [])

  return (
    <div style={{ padding: '2rem', textAlign: 'left' }}>
      <h1>Narrative Atlas</h1>
      <p>Political and media intelligence platform for narrative discovery, semantic analysis and monitoring.</p>
      <h2>Stare backend</h2>
      {error ? (
        <p style={{ color: 'crimson' }}>Backendul nu răspunde: {error}</p>
      ) : (
        <p>Răspuns de la /health: <strong>{status}</strong></p>
      )}
    </div>
  )
}

export default App
