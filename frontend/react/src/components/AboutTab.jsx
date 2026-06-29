import { Activity, Database, Server, Globe, User, ExternalLink } from 'lucide-react'

const TECH_STACK = [
  { name: 'Python 3.11', role: 'Core language' },
  { name: 'FastAPI', role: 'Async REST API' },
  { name: 'scikit-learn', role: 'ML ensemble (GradientBoosting + RandomForest)' },
  { name: 'Prometheus', role: 'Metrics collection' },
  { name: 'Grafana', role: 'Monitoring dashboards (port 3100)' },
  { name: 'React + Vite', role: 'This dashboard' },
  { name: 'Tailwind CSS', role: 'Styling' },
  { name: 'Docker Compose', role: 'Local orchestration' },
  { name: 'DVC', role: 'Data version control + pipeline tracking' },
]

const API_ENDPOINTS = [
  { method: 'GET', path: '/health', description: 'System health check' },
  {
    method: 'POST',
    path: '/predict',
    description: 'Treatment outcome prediction (returns Improvement_Score 0–10)',
  },
  { method: 'GET', path: '/metrics', description: 'Prometheus metrics' },
  { method: 'GET', path: '/dropdown-values', description: 'Valid field values' },
  { method: 'GET', path: '/docs', description: 'Swagger UI' },
]

function SectionCard({ icon: Icon, title, children }) {
  return (
    <div className="rounded-xl border border-slate-700/40 p-6" style={{ backgroundColor: '#161b22' }}>
      <div className="flex items-center gap-2 mb-4">
        <Icon size={18} className="text-blue-400" />
        <h2 className="text-base font-semibold text-slate-100">{title}</h2>
      </div>
      {children}
    </div>
  )
}

function MethodBadge({ method }) {
  const isGet = method === 'GET'
  return (
    <span
      className={`inline-block text-xs font-bold px-2 py-0.5 rounded ${
        isGet
          ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
          : 'bg-green-500/20 text-green-400 border border-green-500/30'
      }`}
    >
      {method}
    </span>
  )
}

export default function AboutTab() {
  return (
    <div className="space-y-6">
      {/* Project Overview */}
      <SectionCard icon={Activity} title="Project Overview">
        <p className="text-slate-300 text-sm leading-relaxed">
          TherapyPred is a production MLOps pipeline that predicts patient treatment
          improvement scores using an ensemble ML model trained on clinical treatment data. Built
          for healthcare research teams and clinical analytics units in European hospitals and
          health insurers.
        </p>
      </SectionCard>

      {/* Tech Stack */}
      <SectionCard icon={Database} title="Tech Stack">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-700/40">
                <th className="text-left text-slate-400 font-medium pb-2 pr-8">Technology</th>
                <th className="text-left text-slate-400 font-medium pb-2">Role</th>
              </tr>
            </thead>
            <tbody>
              {TECH_STACK.map((item, i) => (
                <tr key={i} className="border-b border-slate-700/20 last:border-0">
                  <td className="py-2 pr-8 font-medium text-slate-200 whitespace-nowrap">
                    {item.name}
                  </td>
                  <td className="py-2 text-slate-400">{item.role}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </SectionCard>

      {/* API Reference */}
      <SectionCard icon={Server} title="API Reference">
        <div className="space-y-3">
          {API_ENDPOINTS.map((ep, i) => (
            <div
              key={i}
              className="flex items-start gap-3 rounded-lg border border-slate-700/30 px-4 py-3"
              style={{ backgroundColor: '#0d1117' }}
            >
              <MethodBadge method={ep.method} />
              <code className="text-blue-300 text-sm font-mono whitespace-nowrap">{ep.path}</code>
              <span className="text-slate-400 text-sm">{ep.description}</span>
            </div>
          ))}
        </div>
      </SectionCard>

      {/* Monitoring Links */}
      <SectionCard icon={Globe} title="Monitoring">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <a
            href="http://localhost:3100"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-between rounded-lg border border-slate-700/30 px-4 py-3 hover:border-blue-500/40 transition-colors"
            style={{ backgroundColor: '#0d1117' }}
          >
            <div>
              <div className="text-slate-200 text-sm font-medium">Grafana</div>
              <div className="text-slate-500 text-xs mt-0.5">
                http://localhost:3100 · admin / changeme
              </div>
            </div>
            <ExternalLink size={14} className="text-slate-500 shrink-0" />
          </a>
          <a
            href="http://localhost:9191"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-between rounded-lg border border-slate-700/30 px-4 py-3 hover:border-blue-500/40 transition-colors"
            style={{ backgroundColor: '#0d1117' }}
          >
            <div>
              <div className="text-slate-200 text-sm font-medium">Prometheus</div>
              <div className="text-slate-500 text-xs mt-0.5">http://localhost:9191</div>
            </div>
            <ExternalLink size={14} className="text-slate-500 shrink-0" />
          </a>
        </div>
      </SectionCard>

      {/* Author */}
      <SectionCard icon={User} title="Author">
        <p className="text-slate-300 text-sm">
          Built by{' '}
          <span className="text-slate-100 font-medium">Rayen Lassoued</span>
          {' · '}
          <a
            href="https://github.com/Hamilas"
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-400 hover:text-blue-300 transition-colors"
          >
            github.com/Hamilas
          </a>
          {' · '}
          <a
            href="https://www.linkedin.com/in/lassoued-rayen/"
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-400 hover:text-blue-300 transition-colors"
          >
            https://www.linkedin.com/in/lassoued-rayen/
          </a>
        </p>
      </SectionCard>
    </div>
  )
}
