import { CheckCircle } from 'lucide-react'

const SEV_STYLE = {
  HIGH:   'bg-red-900/70 text-red-300 border border-red-700/50',
  MEDIUM: 'bg-orange-900/60 text-orange-300 border border-orange-700/50',
  LOW:    'bg-blue-900/60 text-blue-300 border border-blue-700/50',
}

const ruleId = (ruleStr = '') => {
  const m = ruleStr.match(/R-\d+/)
  return m ? m[0] : '—'
}

const trunc = (s = '', n = 50) =>
  s.length <= n ? s : s.slice(0, n - 1) + '…'

const SEV_ORDER = { HIGH: 0, MEDIUM: 1, LOW: 2 }

export default function TamperFlagsTable({ flags = [] }) {
  if (!flags.length) {
    return (
      <div className="flex items-center gap-2 rounded-xl border border-green-500/30 bg-green-500/10 px-5 py-4 text-green-400 text-sm">
        <CheckCircle size={16} />
        No tamper flags detected — evidence appears unmodified.
      </div>
    )
  }

  const sorted = [...flags].sort(
    (a, b) => (SEV_ORDER[a.severity] ?? 9) - (SEV_ORDER[b.severity] ?? 9)
  )

  return (
    <div className="rounded-xl border border-slate-700/50 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-900 border-b border-slate-700/60 text-left sticky top-0 z-10">
              <th className="px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider w-16">
                Rule
              </th>
              <th className="px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider w-24">
                Severity
              </th>
              <th className="px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider w-44">
                Type
              </th>
              <th className="px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                File
              </th>
              <th className="px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Detail
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {sorted.map((f, i) => (
              <tr
                key={i}
                className="bg-slate-800/40 hover:bg-slate-800/70 transition-colors"
              >
                <td className="px-4 py-3">
                  <span className="font-mono text-xs px-1.5 py-0.5 rounded bg-slate-700 text-slate-300 border border-slate-600">
                    {ruleId(f.rule)}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`inline-block text-xs font-semibold px-2 py-0.5 rounded ${
                      SEV_STYLE[f.severity] ?? 'bg-slate-700 text-slate-300'
                    }`}
                  >
                    {f.severity}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className="font-mono text-xs text-slate-200">{f.type}</span>
                </td>
                <td className="px-4 py-3 max-w-xs">
                  <span
                    className="font-mono text-xs text-slate-300 block truncate"
                    title={f.file}
                  >
                    {trunc(f.file ?? '', 50)}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className="text-xs text-slate-400 leading-relaxed">
                    {f.detail}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
