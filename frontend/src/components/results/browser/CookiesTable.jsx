import { Check, Minus } from 'lucide-react'
import Badge from '../../ui/Badge'

const SRC_COLOR = { 'Chrome/Edge': 'blue', 'Firefox': 'orange' }

const BoolCell = ({ value }) =>
  value
    ? <Check size={13} className="text-green-400 mx-auto" />
    : <Minus size={13} className="text-slate-600 mx-auto" />

export default function CookiesTable({ cookies = [] }) {
  if (cookies.length === 0) {
    return <p className="text-center text-slate-500 text-xs py-8">No cookies found.</p>
  }

  return (
    <div className="rounded-lg border border-slate-700 overflow-hidden">
      <div className="max-h-96 overflow-y-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-700 sticky top-0 z-10">
              {['#', 'Source', 'Host', 'Cookie Name', 'Expires', 'Secure', 'HttpOnly'].map((h) => (
                <th key={h} className="px-3 py-2.5 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider whitespace-nowrap">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/80">
            {cookies.map((c, i) => (
              <tr key={i} className={`transition-colors hover:bg-slate-700/40 ${i % 2 === 0 ? 'bg-slate-800/40' : 'bg-slate-800/70'}`}>
                <td className="px-3 py-2.5 text-xs text-slate-500 w-10">{i + 1}</td>
                <td className="px-3 py-2.5 w-28">
                  <Badge color={SRC_COLOR[c.source] ?? 'slate'}>{c.source}</Badge>
                </td>
                <td className="px-3 py-2.5 text-xs font-mono text-slate-200 max-w-[10rem] truncate" title={c.host_key}>
                  {c.host_key || '—'}
                </td>
                <td className="px-3 py-2.5 text-xs text-slate-300 max-w-[10rem] truncate" title={c.name}>
                  {c.name || '—'}
                </td>
                <td className="px-3 py-2.5 text-xs font-mono text-slate-400 whitespace-nowrap w-40">
                  {c.expires_utc || '—'}
                </td>
                <td className="px-3 py-2.5 text-center w-16"><BoolCell value={c.is_secure} /></td>
                <td className="px-3 py-2.5 text-center w-20"><BoolCell value={c.is_httponly} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
