export default function Header() {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 py-3 border-b border-slate-700/60"
            style={{ backgroundColor: '#0f172a' }}>
      <span className="font-mono text-xl font-bold tracking-tight text-blue-400">
        ForensIQ
      </span>
      <span className="text-xs font-mono px-2 py-1 rounded bg-slate-800 text-slate-400 border border-slate-700">
        v1.0.0
      </span>
    </header>
  )
}
