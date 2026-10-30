import { useEffect, useState } from 'react'
import './App.css'

const API_URL = 'http://127.0.0.1:8000'
const PAGE_SIZE = 50

function App() {
  const [backendStatus, setBackendStatus] = useState('se verifică...')
  const [parties, setParties] = useState([])
  const [party, setParty] = useState('')
  const [queryInput, setQueryInput] = useState('')
  const [query, setQuery] = useState('')
  const [offset, setOffset] = useState(0)
  const [result, setResult] = useState({ total: 0, items: [] })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch(API_URL + '/health')
      .then((response) => response.json())
      .then((data) => setBackendStatus(data.status))
      .catch(() => setBackendStatus('nu răspunde'))
  }, [])

  useEffect(() => {
    fetch(API_URL + '/parties')
      .then((response) => response.json())
      .then((data) => setParties(Array.isArray(data) ? data : []))
      .catch(() => setParties([]))
  }, [])

  useEffect(() => {
    const params = new URLSearchParams({
      limit: String(PAGE_SIZE),
      offset: String(offset),
    })
    if (party) params.set('party', party)
    if (query) params.set('q', query)

    setLoading(true)
    setError(null)
    fetch(API_URL + '/interpellations?' + params.toString())
      .then((response) => {
        if (!response.ok) {
          throw new Error('Eroare de la server: ' + response.status)
        }
        return response.json()
      })
      .then((data) => setResult(data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [party, query, offset])

  function handleSearch(event) {
    event.preventDefault()
    setOffset(0)
    setQuery(queryInput.trim())
  }

  function handlePartyChange(event) {
    setOffset(0)
    setParty(event.target.value)
  }

  const firstShown = result.total === 0 ? 0 : offset + 1
  const lastShown = Math.min(offset + PAGE_SIZE, result.total)

  return (
    <div style={{ padding: '1.5rem', textAlign: 'left' }}>
      <h1>Narrative Atlas</h1>
      <p>
        Political and media intelligence platform for narrative discovery,
        semantic analysis and monitoring.
      </p>
      <p>
        Stare backend: <strong>{backendStatus}</strong>
      </p>

      <h2>Interpelări, Sejm, legislatura a 8-a</h2>

      <form
        onSubmit={handleSearch}
        style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', marginBottom: '1rem' }}
      >
        <select value={party} onChange={handlePartyChange}>
          <option value="">Toate partidele</option>
          {parties.map((item) => (
            <option key={item.party} value={item.party}>
              {item.party} ({item.count})
            </option>
          ))}
        </select>
        <input
          type="text"
          value={queryInput}
          onChange={(event) => setQueryInput(event.target.value)}
          placeholder="Caută în text..."
          style={{ minWidth: '16rem' }}
        />
        <button type="submit">Caută</button>
      </form>

      {error && <p style={{ color: 'crimson' }}>{error}</p>}
      {loading && <p>Se încarcă...</p>}

      <p>
        {firstShown}-{lastShown} din {result.total} rezultate
      </p>

      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th style={{ textAlign: 'left', padding: '0.4rem' }}>Data</th>
            <th style={{ textAlign: 'left', padding: '0.4rem' }}>Partid</th>
            <th style={{ textAlign: 'left', padding: '0.4rem' }}>MP</th>
            <th style={{ textAlign: 'right', padding: '0.4rem' }}>Cuvinte</th>
            <th style={{ textAlign: 'left', padding: '0.4rem' }}>Text</th>
          </tr>
        </thead>
        <tbody>
          {result.items.map((item, index) => (
            <tr
              key={String(item.term) + '-' + String(item.num) + '-' + String(index)}
              style={{ borderTop: '1px solid #8884' }}
            >
              <td style={{ padding: '0.4rem', whiteSpace: 'nowrap' }}>{item.date}</td>
              <td style={{ padding: '0.4rem' }}>{item.party}</td>
              <td style={{ padding: '0.4rem' }}>{item.mp_id}</td>
              <td style={{ padding: '0.4rem', textAlign: 'right' }}>{item.word_count}</td>
              <td style={{ padding: '0.4rem' }}>
                {item.text && item.text.length > 220
                  ? item.text.slice(0, 220) + '...'
                  : item.text}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem' }}>
        <button
          onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
          disabled={offset === 0}
        >
          Pagina anterioară
        </button>
        <button
          onClick={() => setOffset(offset + PAGE_SIZE)}
          disabled={offset + PAGE_SIZE >= result.total}
        >
          Pagina următoare
        </button>
      </div>
    </div>
  )
}

export default App

// sfârșit fișier

