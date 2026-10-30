import { useEffect, useState } from 'react'
import './App.css'

const API_URL = 'http://127.0.0.1:8000'
const PAGE_SIZE = 50

function sourceLabel(source) {
  if (source === 'sejm_list') return 'Sejm list'
  if (source === 'merged_label') return 'merged'
  if (source === 'unresolved') return 'unresolved'
  return ''
}

// Short axis label for a quarter such as "2016-Q3" -> "16 Q3".
function shortQuarter(label) {
  return label.slice(2, 4) + ' ' + label.slice(5)
}

function TimelineChart({ quarters }) {
  if (!quarters || quarters.length === 0) {
    return <p>No data for this selection.</p>
  }

  const width = 760
  const height = 260
  const left = 48
  const right = 10
  const top = 14
  const bottom = 46
  const plotWidth = width - left - right
  const plotHeight = height - top - bottom

  const maxCount = Math.max(...quarters.map((q) => q.count), 1)
  const step = Math.pow(10, Math.floor(Math.log10(maxCount))) / 2
  const niceMax = Math.ceil(maxCount / step) * step
  const ticks = [0, 1, 2, 3, 4].map((i) => Math.round((niceMax * i) / 4))

  const slot = plotWidth / quarters.length
  const barWidth = slot * 0.7

  return (
    <svg
      viewBox={'0 0 ' + width + ' ' + height}
      style={{ width: '100%', maxWidth: '760px', height: 'auto' }}
      role="img"
      aria-label="Interpellations per quarter"
    >
      {ticks.map((tick) => {
        const y = top + plotHeight - (tick / niceMax) * plotHeight
        return (
          <g key={tick}>
            <line x1={left} x2={width - right} y1={y} y2={y} stroke="currentColor" opacity="0.15" />
            <text x={left - 6} y={y + 4} textAnchor="end" fontSize="11" fill="currentColor" opacity="0.7">
              {tick}
            </text>
          </g>
        )
      })}
      {quarters.map((item, index) => {
        const barHeight = (item.count / niceMax) * plotHeight
        const x = left + index * slot + (slot - barWidth) / 2
        const y = top + plotHeight - barHeight
        const partial = index === 0 || index === quarters.length - 1
        return (
          <g key={item.quarter}>
            <rect
              x={x}
              y={y}
              width={barWidth}
              height={barHeight}
              fill="#4f7cff"
              opacity={partial ? 0.45 : 0.9}
            >
              <title>{item.quarter + ': ' + item.count + ' interpellations'}</title>
            </rect>
            <text
              x={x + barWidth / 2}
              y={top + plotHeight + 14}
              textAnchor="middle"
              fontSize="10"
              fill="currentColor"
              opacity="0.8"
            >
              {shortQuarter(item.quarter) + (partial ? '*' : '')}
            </text>
          </g>
        )
      })}
    </svg>
  )
}

function App() {
  const [backendStatus, setBackendStatus] = useState('checking...')
  const [quality, setQuality] = useState(null)
  const [parties, setParties] = useState([])
  const [party, setParty] = useState('')
  const [queryInput, setQueryInput] = useState('')
  const [query, setQuery] = useState('')
  const [hideRepeats, setHideRepeats] = useState(false)
  const [offset, setOffset] = useState(0)
  const [result, setResult] = useState({ total: 0, items: [] })
  const [timeline, setTimeline] = useState({ total: 0, quarters: [] })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch(API_URL + '/health')
      .then((response) => response.json())
      .then((data) => setBackendStatus(data.status))
      .catch(() => setBackendStatus('not responding'))
  }, [])

  useEffect(() => {
    fetch(API_URL + '/data-quality')
      .then((response) => response.json())
      .then((data) => setQuality(data))
      .catch(() => setQuality(null))
  }, [])

  useEffect(() => {
    fetch(API_URL + '/parties')
      .then((response) => response.json())
      .then((data) => setParties(Array.isArray(data) ? data : []))
      .catch(() => setParties([]))
  }, [])

  useEffect(() => {
    const params = new URLSearchParams()
    if (party) params.set('party', party)
    if (hideRepeats) params.set('hide_repeats', 'true')

    fetch(API_URL + '/timeline?' + params.toString())
      .then((response) => response.json())
      .then((data) => setTimeline(data))
      .catch(() => setTimeline({ total: 0, quarters: [] }))
  }, [party, hideRepeats])

  useEffect(() => {
    const params = new URLSearchParams({
      limit: String(PAGE_SIZE),
      offset: String(offset),
    })
    if (party) params.set('party', party)
    if (query) params.set('q', query)
    if (hideRepeats) params.set('hide_repeats', 'true')

    setLoading(true)
    setError(null)
    fetch(API_URL + '/interpellations?' + params.toString())
      .then((response) => {
        if (!response.ok) {
          throw new Error('Server error: ' + response.status)
        }
        return response.json()
      })
      .then((data) => setResult(data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [party, query, hideRepeats, offset])

  function handleSearch(event) {
    event.preventDefault()
    setOffset(0)
    setQuery(queryInput.trim())
  }

  function handlePartyChange(event) {
    setOffset(0)
    setParty(event.target.value)
  }

  function handleHideRepeatsChange(event) {
    setOffset(0)
    setHideRepeats(event.target.checked)
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
        Backend status: <strong>{backendStatus}</strong>
      </p>

      {quality && (
        <div>
          <p>
            Data quality: <strong>{quality.total_records}</strong> records,{' '}
            <strong>{quality.repeat_records}</strong> repeated (same date, MP and
            text).
          </p>
          <p>
            Party: <strong>{quality.party_from_data}</strong> from the data,{' '}
            <strong>{quality.party_from_sejm_list}</strong> filled from the Sejm
            MP list, <strong>{quality.party_from_merged_label}</strong> merged
            from the KO label,{' '}
            <strong>{quality.party_unresolved_records}</strong> unresolved.
          </p>
          {!quality.sejm_list_loaded && (
            <p style={{ color: 'crimson' }}>
              The Sejm MP list was not found, so missing parties are not filled in.
            </p>
          )}
        </div>
      )}

      <h2>Interpellations, Sejm, 8th term</h2>

      <form
        onSubmit={handleSearch}
        style={{
          display: 'flex',
          gap: '0.75rem',
          flexWrap: 'wrap',
          alignItems: 'center',
          marginBottom: '1rem',
        }}
      >
        <select value={party} onChange={handlePartyChange}>
          <option value="">All parties</option>
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
          placeholder="Search in text..."
          style={{ minWidth: '16rem' }}
        />
        <button type="submit">Search</button>
        <label>
          <input
            type="checkbox"
            checked={hideRepeats}
            onChange={handleHideRepeatsChange}
          />{' '}
          Hide repeated interpellations
        </label>
      </form>

      <h3>
        Interpellations per quarter ({party || 'all parties'}
        {hideRepeats ? ', without repeats' : ''}): {timeline.total}
      </h3>
      <TimelineChart quarters={timeline.quarters} />
      <p style={{ fontSize: '0.85rem', opacity: 0.7 }}>
        * Partial quarters: the term began in November 2015 and ended in autumn
        2019. The chart follows the party and repeat filters above; the text
        search only affects the table.
      </p>

      {error && <p style={{ color: 'crimson' }}>{error}</p>}
      {loading && <p>Loading...</p>}

      <p>
        {firstShown}-{lastShown} of {result.total} results
      </p>

      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th style={{ textAlign: 'left', padding: '0.4rem' }}>Date</th>
            <th style={{ textAlign: 'left', padding: '0.4rem' }}>Party</th>
            <th style={{ textAlign: 'left', padding: '0.4rem' }}>MP</th>
            <th style={{ textAlign: 'right', padding: '0.4rem' }}>Words</th>
            <th style={{ textAlign: 'right', padding: '0.4rem' }}>Repeats</th>
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
              <td
                style={{ padding: '0.4rem', whiteSpace: 'nowrap' }}
                title={'Original party in the data: ' + String(item.party)}
              >
                {item.party_resolved}
                {sourceLabel(item.party_source) && (
                  <small style={{ opacity: 0.7 }}>
                    {' '}
                    ({sourceLabel(item.party_source)})
                  </small>
                )}
              </td>
              <td style={{ padding: '0.4rem' }}>{item.mp_id}</td>
              <td style={{ padding: '0.4rem', textAlign: 'right' }}>{item.word_count}</td>
              <td style={{ padding: '0.4rem', textAlign: 'right' }}>
                {item.repeat_count > 1 ? 'x' + item.repeat_count : ''}
              </td>
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
          Previous page
        </button>
        <button
          onClick={() => setOffset(offset + PAGE_SIZE)}
          disabled={offset + PAGE_SIZE >= result.total}
        >
          Next page
        </button>
      </div>
    </div>
  )
}

export default App

// end of file