import React, { useState } from 'react'
import Dashboard from './components/Dashboard.jsx'
import PredictTab from './components/PredictTab.jsx'
import AboutTab from './components/AboutTab.jsx'

const NAV_TABS = [
  { id: 'dashboard', label: 'Dashboard', icon: (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
      <rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
    </svg>
  )},
  { id: 'predict', label: 'Predict', icon: (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2v-4M9 21H5a2 2 0 0 1-2-2v-4m0 0h18"/>
    </svg>
  )},
  { id: 'about', label: 'About', icon: (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>
    </svg>
  )},
]

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard')

  return (
    <div className="min-h-screen" style={{ backgroundColor: '#0a0f1a', fontFamily: "'Inter', sans-serif" }}>

      {/* Top accent line */}
      <div style={{ height: '2px', background: '#3b82f6' }} />

      {/* Header */}
      <header style={{ backgroundColor: 'rgba(15,23,42,0.95)', borderBottom: '1px solid rgba(51,65,85,0.4)', backdropFilter: 'blur(12px)', position: 'sticky', top: 0, zIndex: 50 }}>
        <div className="max-w-6xl mx-auto px-6">
          <div className="flex items-center justify-between h-14">

            {/* Brand */}
            <div className="flex items-center gap-3">
              <div style={{ width: 34, height: 34, borderRadius: 9, background: 'rgba(59,130,246,0.2)', border: '1px solid rgba(59,130,246,0.35)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
                </svg>
              </div>
              <div>
                <span className="font-bold text-slate-100" style={{ fontSize: 16, letterSpacing: '-0.01em' }}>
                  Therapy<span style={{ color: '#60a5fa' }}>Pred</span>
                </span>
                <span className="ml-2 text-slate-600" style={{ fontSize: 10, letterSpacing: '0.12em', textTransform: 'uppercase', fontWeight: 500 }}>
                  MLOps
                </span>
              </div>
            </div>

            {/* Nav */}
            <nav className="flex items-center gap-1">
              {NAV_TABS.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-150"
                  style={activeTab === tab.id
                    ? { background: 'rgba(59,130,246,0.15)', color: '#60a5fa', border: '1px solid rgba(59,130,246,0.3)' }
                    : { color: '#64748b', border: '1px solid transparent' }
                  }
                >
                  {tab.icon}
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="max-w-6xl mx-auto px-6 py-8">
        {activeTab === 'dashboard' && <Dashboard />}
        {activeTab === 'predict'   && <PredictTab />}
        {activeTab === 'about'     && <AboutTab />}
      </main>
    </div>
  )
}
