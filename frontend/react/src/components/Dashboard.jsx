import React, { useState, useEffect, useCallback } from 'react'

function parsePrometheusMetrics(text) {
  const result = {}
  if (!text) return result
  for (const line of text.split('\n')) {
    const t = line.trim()
    if (!t || t.startsWith('#')) continue
    const i = t.lastIndexOf(' ')
    if (i === -1) continue
    const key = t.slice(0, i).replace(/\{[^}]*\}/g, '').trim()
    const val = parseFloat(t.slice(i + 1))
    if (!isNaN(val)) result[key] = val
  }
  return result
}

const CONDITION_COLORS = {
  Depression: '#8b5cf6', Diabetes: '#06b6d4',
  Hypertension: '#ef4444', Infection: '#f59e0b', 'Pain Relief': '#10b981',
}

export default function Dashboard() {
  const [health, setHealth]       = useState(null)
  const [healthErr, setHealthErr] = useState(null)
  const [metrics, setMetrics]     = useState(null)
  const [dropdowns, setDropdowns] = useState(null)
  const [lastUpdated, setLast]    = useState(null)
  const [loading, setLoading]     = useState(false)

  const fetchAll = useCallback(async () => {
    setLoading(true)
    try {
      try {
        const r = await fetch('/api/health')
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        setHealth(await r.json()); setHealthErr(null)
      } catch (e) { setHealthErr(e.message); setHealth(null) }

      try {
        const r = await fetch('/api/metrics')
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        setMetrics(parsePrometheusMetrics(await r.text()))
      } catch { setMetrics(null) }

      try {
        const r = await fetch('/api/dropdown-values')
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        setDropdowns(await r.json())
      } catch { setDropdowns(null) }

      setLast(new Date())
    } finally { setLoading(false) }
  }, [])

  useEffect(() => {
    fetchAll()
    const t = setInterval(fetchAll, 15000)
    return () => clearInterval(t)
  }, [fetchAll])

  const isOnline = health && !healthErr
  const totalPredictions = metrics?.['api_prediction_total'] ?? null
  const totalErrors      = metrics?.['api_prediction_errors_total'] ?? null
  const totalRequests    = metrics?.['api_request_total'] ?? null

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>

      {/* Page header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: '#f1f5f9', margin: 0 }}>System Dashboard</h1>
          <p style={{ fontSize: 13, color: '#475569', marginTop: 4 }}>
            Live status of the TherapyPred inference backend
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          {lastUpdated && (
            <span style={{ fontSize: 11, color: '#334155', fontFamily: 'monospace' }}>
              {lastUpdated.toLocaleTimeString()}
            </span>
          )}
          <button
            onClick={fetchAll} disabled={loading}
            style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '6px 12px', borderRadius: 8, background: 'rgba(59,130,246,0.08)', border: '1px solid rgba(59,130,246,0.2)', color: '#60a5fa', fontSize: 12, fontWeight: 500, cursor: 'pointer' }}
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={loading ? { animation: 'spin 1s linear infinite' } : {}}>
              <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/>
              <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/>
            </svg>
            Refresh
          </button>
        </div>
      </div>

      {/* KPI row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
        {[
          { label: 'API Status', value: isOnline ? 'Healthy' : healthErr ? 'Unreachable' : '…', color: isOnline ? '#10b981' : '#f59e0b', bg: isOnline ? 'rgba(16,185,129,0.08)' : 'rgba(245,158,11,0.08)', border: isOnline ? 'rgba(16,185,129,0.25)' : 'rgba(245,158,11,0.25)', dot: true },
          { label: 'Model Loaded', value: health ? (health.model_loaded ? 'Yes' : 'No') : '…', color: health?.model_loaded ? '#10b981' : '#ef4444', bg: 'rgba(15,23,42,0.6)', border: 'rgba(51,65,85,0.4)' },
          { label: 'Predictions Served', value: totalPredictions !== null ? totalPredictions.toLocaleString() : '…', color: '#60a5fa', bg: 'rgba(59,130,246,0.06)', border: 'rgba(59,130,246,0.2)' },
          { label: 'Prediction Errors', value: totalErrors !== null ? totalErrors.toLocaleString() : '…', color: totalErrors > 0 ? '#ef4444' : '#10b981', bg: 'rgba(15,23,42,0.6)', border: 'rgba(51,65,85,0.4)' },
        ].map((k) => (
          <div key={k.label} style={{ background: k.bg, border: `1px solid ${k.border}`, borderRadius: 12, padding: '18px 20px' }}>
            <div style={{ fontSize: 11, color: '#475569', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600 }}>{k.label}</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              {k.dot && <span style={{ width: 8, height: 8, borderRadius: '50%', background: k.color, boxShadow: `0 0 6px ${k.color}` }} />}
              <span style={{ fontSize: 22, fontWeight: 700, color: k.color, fontFamily: 'monospace' }}>{k.value}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Model info + dataset stats */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>

        {/* Model info */}
        <div style={{ background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(51,65,85,0.4)', borderRadius: 12, padding: 24 }}>
          <h2 style={{ fontSize: 12, fontWeight: 600, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 16 }}>Model Details</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {[
              { k: 'Algorithm',    v: 'RandomForestRegressor' },
              { k: 'Version',      v: health?.model_version ?? '—' },
              { k: 'Training set', v: '800 patient records' },
              { k: 'Test set',     v: '200 patient records' },
              { k: 'Framework',    v: 'scikit-learn + joblib' },
            ].map(({ k, v }) => (
              <div key={k} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: 10, borderBottom: '1px solid rgba(51,65,85,0.25)' }}>
                <span style={{ fontSize: 13, color: '#64748b' }}>{k}</span>
                <span style={{ fontSize: 12, color: '#e2e8f0', fontFamily: 'monospace', background: 'rgba(51,65,85,0.3)', padding: '2px 8px', borderRadius: 5 }}>{v}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Dataset coverage */}
        <div style={{ background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(51,65,85,0.4)', borderRadius: 12, padding: 24 }}>
          <h2 style={{ fontSize: 12, fontWeight: 600, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 16 }}>Dataset Coverage</h2>
          {dropdowns ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {[
                { label: 'Conditions', count: dropdowns.conditions?.length, items: dropdowns.conditions, color: '#8b5cf6' },
                { label: 'Drugs',      count: dropdowns.drugs?.length,      items: dropdowns.drugs?.slice(0,4), color: '#06b6d4' },
                { label: 'Side Effects', count: dropdowns.side_effects?.length, items: null, color: '#f59e0b' },
                { label: 'Valid Combos', count: dropdowns.valid_combinations?.length, items: null, color: '#10b981' },
              ].map(({ label, count, items, color }) => (
                <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <span style={{ fontSize: 22, fontWeight: 700, color, fontFamily: 'monospace', minWidth: 36, textAlign: 'right' }}>{count ?? '—'}</span>
                  <div>
                    <div style={{ fontSize: 13, color: '#94a3b8', fontWeight: 500 }}>{label}</div>
                    {items && <div style={{ fontSize: 11, color: '#334155', marginTop: 1 }}>{items.join(', ')}{dropdowns[label?.toLowerCase()]?.length > 4 ? '…' : ''}</div>}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {[...Array(4)].map((_, i) => <div key={i} style={{ height: 32, borderRadius: 6, background: 'rgba(51,65,85,0.3)', animation: 'pulse 1.5s ease-in-out infinite' }} />)}
            </div>
          )}
        </div>
      </div>

      {/* Conditions breakdown */}
      {dropdowns?.conditions && (
        <div style={{ background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(51,65,85,0.4)', borderRadius: 12, padding: 24 }}>
          <h2 style={{ fontSize: 12, fontWeight: 600, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 16 }}>Supported Conditions</h2>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            {dropdowns.conditions.map((c) => (
              <div key={c} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 16px', borderRadius: 10, background: `${CONDITION_COLORS[c] ?? '#475569'}12`, border: `1px solid ${CONDITION_COLORS[c] ?? '#475569'}35` }}>
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: CONDITION_COLORS[c] ?? '#475569', flexShrink: 0 }} />
                <span style={{ fontSize: 13, color: '#e2e8f0', fontWeight: 500 }}>{c}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <p style={{ fontSize: 11, color: '#1e293b', textAlign: 'center' }}>Auto-refreshes every 15 seconds</p>

      <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
    </div>
  )
}
