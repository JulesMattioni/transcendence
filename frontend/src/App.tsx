const services = [
  { name: 'auth', label: 'Authentication' },
  { name: 'org', label: 'Organizations & RBAC' },
  { name: 'core', label: 'Profiles & Documents' },
  { name: 'rag', label: 'RAG Assistant' },
  { name: 'realtime', label: 'Real-time / WebSockets' },
]

function App() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center px-6">
      <main className="w-full max-w-2xl text-center">
        <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-slate-700 bg-slate-900 px-4 py-1.5 text-xs font-medium text-slate-400">
          <span className="h-2 w-2 rounded-full bg-emerald-400" />
          Work in progress
        </div>

        <h1 className="text-5xl font-bold tracking-tight sm:text-6xl">
          Secure<span className="text-emerald-400">Vault</span>
        </h1>

        <p className="mt-4 text-lg text-slate-400">
          Secure team document vault with role-based access, live audit, and a
          permission-aware AI assistant.
        </p>

        <div className="mt-10 grid grid-cols-2 gap-3 sm:grid-cols-3">
          {services.map((service) => (
            <div
              key={service.name}
              className="rounded-lg border border-slate-800 bg-slate-900 px-4 py-3 text-left transition-colors hover:border-emerald-500/50"
            >
              <p className="font-mono text-sm text-emerald-400">
                {service.name}
              </p>
              <p className="mt-0.5 text-xs text-slate-500">{service.label}</p>
            </div>
          ))}
        </div>

        <p className="mt-10 text-xs text-slate-600">
          Placeholder page — frontend scaffold ready.
        </p>
      </main>
    </div>
  )
}

export default App
