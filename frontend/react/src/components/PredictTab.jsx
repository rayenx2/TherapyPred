import { useState } from "react"

const CONDITIONS = ["Depression", "Diabetes", "Hypertension", "Infection", "Pain Relief"]

const DRUGS_BY_CONDITION = {
  "Depression":   ["Bupropion", "Escitalopram", "Sertraline"],
  "Diabetes":     ["Glipizide", "Insulin Glargine", "Metformin"],
  "Hypertension": ["Amlodipine", "Losartan", "Metoprolol"],
  "Infection":    ["Amoxicillin", "Azithromycin", "Ciprofloxacin"],
  "Pain Relief":  ["Ibuprofen", "Paracetamol", "Tramadol"],
}

const SIDE_EFFECTS_BY_DRUG = {
  "Bupropion":        ["Anxiety", "Dry mouth", "Headache"],
  "Escitalopram":     ["Nausea", "Sleep issues", "Sweating"],
  "Sertraline":       ["Drowsiness", "Dry mouth", "Insomnia"],
  "Glipizide":        ["Low blood sugar", "Nausea", "Skin rash"],
  "Insulin Glargine": ["Injection site pain", "Low sugar", "Weight gain"],
  "Metformin":        ["Diarrhea", "Nausea", "Stomach upset"],
  "Amlodipine":       ["Dizziness", "Fatigue", "Swelling"],
  "Losartan":         ["Back pain", "Cough", "Headache"],
  "Metoprolol":       ["Dizziness", "Slow heartbeat", "Tiredness"],
  "Amoxicillin":      ["Allergy", "Diarrhea", "Rash"],
  "Azithromycin":     ["Abdominal pain", "Headache", "Nausea"],
  "Ciprofloxacin":    ["Dizziness", "Joint pain", "Nausea"],
  "Ibuprofen":        ["Heartburn", "Nausea", "Stomach pain"],
  "Paracetamol":      ["Fatigue", "Liver issues", "Rash"],
  "Tramadol":         ["Constipation", "Dizziness", "Nausea"],
}

const CONDITION_COLORS = {
  Depression: '#8b5cf6', Diabetes: '#06b6d4',
  Hypertension: '#ef4444', Infection: '#f59e0b', 'Pain Relief': '#10b981',
}

const DEFAULT_FORM = {
  Age: 45, Gender: "Male",
  Condition: "Depression", Drug_Name: "Bupropion",
  Dosage_mg: 100, Treatment_Duration_days: 30, Side_Effects: "Dry mouth",
}

function scoreLabel(s) {
  if (s >= 8) return { text: 'Excellent outcome', color: '#10b981', bg: 'rgba(16,185,129,0.1)', border: 'rgba(16,185,129,0.3)' }
  if (s >= 6) return { text: 'Good improvement', color: '#60a5fa', bg: 'rgba(59,130,246,0.1)', border: 'rgba(59,130,246,0.3)' }
  if (s >= 4) return { text: 'Moderate improvement', color: '#f59e0b', bg: 'rgba(245,158,11,0.1)', border: 'rgba(245,158,11,0.3)' }
  return       { text: 'Low improvement expected', color: '#ef4444', bg: 'rgba(239,68,68,0.1)', border: 'rgba(239,68,68,0.3)' }
}

const INPUT = {
  background: 'rgba(15,23,42,0.8)', border: '1px solid rgba(51,65,85,0.6)',
  borderRadius: 8, padding: '9px 12px', color: '#e2e8f0',
  fontSize: 13, width: '100%', outline: 'none',
}

function Field({ label, children }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      <label style={{ fontSize: 11, fontWeight: 600, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.07em' }}>{label}</label>
      {children}
    </div>
  )
}

export default function PredictTab() {
  const [form, setForm]     = useState(DEFAULT_FORM)
  const [loading, setLoading] = useState(false)
  const [result, setResult]   = useState(null)
  const [error, setError]     = useState(null)

  function handleChange(e) {
    const { name, value, type } = e.target
    setForm((p) => ({ ...p, [name]: type === 'number' ? Number(value) : value }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null); setResult(null); setLoading(true)
    try {
      const res = await fetch('/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          Age: Number(form.Age), Gender: form.Gender,
          Condition: form.Condition, Drug_Name: form.Drug_Name,
          Dosage_mg: Number(form.Dosage_mg),
          Treatment_Duration_days: Number(form.Treatment_Duration_days),
          Side_Effects: form.Side_Effects,
        }),
      })
      if (!res.ok) { const d = await res.json().catch(() => ({})); throw new Error(d.detail || `Error ${res.status}`) }
      setResult(await res.json())
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const condColor  = CONDITION_COLORS[form.Condition] ?? '#60a5fa'
  const interp     = result ? scoreLabel(result.Improvement_Score) : null
  const scoreWidth = result ? Math.min(100, (result.Improvement_Score / 10) * 100) : 0

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 420px', gap: 24, alignItems: 'start' }}>

      {/* Left: form */}
      <div style={{ background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(51,65,85,0.4)', borderRadius: 14, padding: 28 }}>
        <div style={{ marginBottom: 24 }}>
          <h1 style={{ fontSize: 18, fontWeight: 700, color: '#f1f5f9', margin: 0 }}>Treatment Outcome Prediction</h1>
          <p style={{ fontSize: 13, color: '#475569', marginTop: 6 }}>
            Enter patient and treatment details to predict the improvement score.
          </p>
        </div>

        {error && (
          <div style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 8, padding: '10px 14px', marginBottom: 20, fontSize: 13, color: '#fca5a5' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {/* Active condition indicator */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 20, padding: '8px 14px', borderRadius: 8, background: `${condColor}10`, border: `1px solid ${condColor}30` }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: condColor }} />
            <span style={{ fontSize: 12, color: condColor, fontWeight: 600 }}>{form.Condition}</span>
            <span style={{ fontSize: 12, color: '#334155', marginLeft: 4 }}>→ {form.Drug_Name} · {form.Dosage_mg}mg · {form.Treatment_Duration_days}d</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>

            <Field label="Age">
              <input type="number" name="Age" value={form.Age} onChange={handleChange} min={18} max={79} style={INPUT} />
            </Field>

            <Field label="Gender">
              <select name="Gender" value={form.Gender} onChange={handleChange} style={INPUT}>
                <option value="Male">Male</option>
                <option value="Female">Female</option>
              </select>
            </Field>

            <Field label="Condition">
              <select name="Condition" value={form.Condition} onChange={(e) => {
                const c = e.target.value
                const d = DRUGS_BY_CONDITION[c]?.[0] ?? ""
                const s = SIDE_EFFECTS_BY_DRUG[d]?.[0] ?? ""
                setForm((p) => ({ ...p, Condition: c, Drug_Name: d, Side_Effects: s }))
              }} style={INPUT}>
                {CONDITIONS.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </Field>

            <Field label="Drug Name">
              <select name="Drug_Name" value={form.Drug_Name} onChange={(e) => {
                const d = e.target.value
                const s = SIDE_EFFECTS_BY_DRUG[d]?.[0] ?? ""
                setForm((p) => ({ ...p, Drug_Name: d, Side_Effects: s }))
              }} style={INPUT}>
                {(DRUGS_BY_CONDITION[form.Condition] ?? []).map((d) => <option key={d} value={d}>{d}</option>)}
              </select>
            </Field>

            <Field label="Dosage (mg)">
              <select name="Dosage_mg" value={form.Dosage_mg} onChange={(e) => setForm((p) => ({ ...p, Dosage_mg: Number(e.target.value) }))} style={INPUT}>
                {[50, 100, 250, 500, 850].map((v) => <option key={v} value={v}>{v} mg</option>)}
              </select>
            </Field>

            <Field label="Treatment Duration (days)">
              <input type="number" name="Treatment_Duration_days" value={form.Treatment_Duration_days} onChange={handleChange} min={5} max={59} style={INPUT} />
            </Field>

            <Field label="Side Effects" >
              <select name="Side_Effects" value={form.Side_Effects} onChange={handleChange} style={{ ...INPUT, gridColumn: '1 / -1' }}>
                {(SIDE_EFFECTS_BY_DRUG[form.Drug_Name] ?? []).map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </Field>

          </div>

          <button
            type="submit" disabled={loading}
            style={{
              width: '100%', padding: '11px 0', borderRadius: 9, fontWeight: 600, fontSize: 14,
              background: loading ? 'rgba(59,130,246,0.3)' : '#3b82f6',
              color: loading ? '#93c5fd' : '#fff', border: 'none', cursor: loading ? 'not-allowed' : 'pointer',
              transition: 'all 0.2s', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
            }}
          >
            {loading ? (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ animation: 'spin 1s linear infinite' }}>
                  <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
                </svg>
                Predicting…
              </>
            ) : (
              <>
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <polygon points="5 3 19 12 5 21 5 3"/>
                </svg>
                Predict Outcome
              </>
            )}
          </button>
        </form>
      </div>

      {/* Right: result */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

        {/* Result card */}
        {result && interp ? (
          <div style={{ background: 'rgba(15,23,42,0.7)', border: `1px solid ${interp.border}`, borderRadius: 14, padding: 28, animation: 'fadeIn 0.3s ease-out' }}>
            <div style={{ textAlign: 'center', marginBottom: 24 }}>
              <p style={{ fontSize: 11, fontWeight: 600, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 12 }}>
                Improvement Score
              </p>
              <div style={{ fontSize: 64, fontWeight: 800, color: interp.color, fontFamily: 'monospace', lineHeight: 1 }}>
                {result.Improvement_Score.toFixed(2)}
              </div>
              <div style={{ fontSize: 18, color: '#334155', fontFamily: 'monospace', marginTop: 4 }}>/ 10</div>
            </div>

            {/* Score bar */}
            <div style={{ height: 8, borderRadius: 99, background: 'rgba(51,65,85,0.5)', overflow: 'hidden', marginBottom: 16 }}>
              <div style={{ height: '100%', borderRadius: 99, background: interp.color, width: `${scoreWidth}%`, transition: 'width 0.8s ease-out', boxShadow: `0 0 10px ${interp.color}60` }} />
            </div>

            {/* Badge */}
            <div style={{ textAlign: 'center', marginBottom: 20 }}>
              <span style={{ display: 'inline-block', padding: '6px 16px', borderRadius: 99, background: interp.bg, border: `1px solid ${interp.border}`, color: interp.color, fontSize: 13, fontWeight: 600 }}>
                {interp.text}
              </span>
            </div>

            {/* Summary */}
            <div style={{ background: 'rgba(51,65,85,0.15)', borderRadius: 10, padding: 16, display: 'flex', flexDirection: 'column', gap: 10 }}>
              {[
                { k: 'Condition', v: form.Condition },
                { k: 'Drug',      v: `${form.Drug_Name} · ${form.Dosage_mg}mg` },
                { k: 'Duration',  v: `${form.Treatment_Duration_days} days` },
                { k: 'Side Effect', v: form.Side_Effects },
                { k: 'Model',     v: result.model_version },
              ].map(({ k, v }) => (
                <div key={k} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12 }}>
                  <span style={{ color: '#475569' }}>{k}</span>
                  <span style={{ color: '#94a3b8', fontFamily: 'monospace' }}>{v}</span>
                </div>
              ))}
            </div>

            <p style={{ fontSize: 11, color: '#1e3a5f', marginTop: 16, lineHeight: 1.6, textAlign: 'center' }}>
              {result.disclaimer}
            </p>
          </div>
        ) : (
          <div style={{ background: 'rgba(15,23,42,0.5)', border: '1px solid rgba(51,65,85,0.3)', borderRadius: 14, padding: 40, textAlign: 'center' }}>
            <div style={{ width: 52, height: 52, borderRadius: '50%', background: 'rgba(59,130,246,0.08)', border: '1px solid rgba(59,130,246,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
              </svg>
            </div>
            <p style={{ fontSize: 14, color: '#334155', fontWeight: 500 }}>No prediction yet</p>
            <p style={{ fontSize: 12, color: '#1e293b', marginTop: 6 }}>Fill in the form and click Predict Outcome</p>
          </div>
        )}

        {/* Quick guide */}
        <div style={{ background: 'rgba(15,23,42,0.5)', border: '1px solid rgba(51,65,85,0.3)', borderRadius: 12, padding: 18 }}>
          <p style={{ fontSize: 11, fontWeight: 600, color: '#334155', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 12 }}>How it works</p>
          {[
            ['1', 'Select a condition, then the drug list updates automatically'],
            ['2', 'Pick drug and dosage, side effects update to match'],
            ['3', 'Set age, gender and treatment duration'],
            ['4', 'Click Predict, the RandomForest model scores 0 to 10'],
          ].map(([n, t]) => (
            <div key={n} style={{ display: 'flex', gap: 10, marginBottom: 8 }}>
              <span style={{ width: 18, height: 18, borderRadius: '50%', background: 'rgba(59,130,246,0.15)', border: '1px solid rgba(59,130,246,0.25)', color: '#60a5fa', fontSize: 10, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>{n}</span>
              <span style={{ fontSize: 12, color: '#475569', lineHeight: 1.5 }}>{t}</span>
            </div>
          ))}
        </div>
      </div>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg) } }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(8px) } to { opacity: 1; transform: translateY(0) } }
        select option { background: #0f172a; color: #e2e8f0; }
        input[type=number]::-webkit-inner-spin-button { opacity: 0.3 }
      `}</style>
    </div>
  )
}
