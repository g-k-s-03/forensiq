import { CheckCircle } from 'lucide-react'
import Badge from '../ui/Badge'

const SEV_COLOR = { HIGH: 'red', MEDIUM: 'orange', LOW: 'blue' }
const SEV_ORDER = { HIGH: 0, MEDIUM: 1, LOW: 2 }

const ruleId = (ruleStr = '') => {
  const m = ruleStr.match(/R-\d+/)
  return m ? m[0] : '—'
}

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
              {['Rule', 'Severity', 'Type', 'File', 'Detail'].map((h) => (
                <th key={h} className="px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {sorted.map((f, i) => (
              <tr key={i} className="bg-slate-800/40 hover:bg-slate-800/70 transition-colors">
                <td className="px-4 py-3 w-16">
                  <Badge color="slate">
                    <span className="font-mono">{ruleId(f.rule)}</span>
                  </Badge>
                </td>
                <td className="px-4 py-3 w-24">
                  <Badge color={SEV_COLOR[f.severity] ?? 'slate'}>{f.severity}</Badge>
                </td>
                <td className="px-4 py-3 w-44">
                  <span className="font-mono text-xs text-slate-200">{f.type}</span>
                </td>
                <td className="px-4 py-3 max-w-xs">
                  <span className="font-mono text-xs text-slate-300 block truncate" title={f.file}>
                    {f.file && f.file.length > 50 ? f.file.slice(0, 49) + '…' : (f.file ?? '—')}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className="text-xs text-slate-400 leading-relaxed">{f.detail}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
