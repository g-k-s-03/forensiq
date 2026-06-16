import { Info } from 'lucide-react'

export default function DnsCacheTable({ dnsCcache = [] }) {
  return (
    <div className="flex flex-col gap-3">
      {/* INFERRED note */}
      <div className="flex items-start gap-2 rounded-lg border border-yellow-500/30 bg-yellow-500/10 px-4 py-3 text-xs text-yellow-400">
        <Info size={13} className="mt-0.5 shrink-0" />
        <span>
          DNS cache entries reflect hostnames resolved on the examined machine at time of
          analysis. These are <strong>INFERRED</strong> artifacts and do not constitute
          confirmed browsing activity.
        </span>
      </div>

      {/* Table */}
      {dnsCcache.length === 0 ? (
        <p className="text-center text-slate-500 text-xs py-8">No DNS cache entries found.</p>
      ) : (
        <div className="rounded-lg border border-slate-700 overflow-hidden">
          <div className="max-h-96 overflow-y-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-700 sticky top-0 z-10">
                  {['#', 'Hostname', 'Detail'].map((h) => (
                    <th
                      key={h}
                      className="px-3 py-2.5 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                {dnsCcache.map((e, i) => (
                  <tr
                    key={i}
                    className={`transition-colors hover:bg-slate-700/40 ${
                      i % 2 === 0 ? 'bg-slate-800/40' : 'bg-slate-800/70'
                    }`}
                  >
                    <td className="px-3 py-2.5 text-xs text-slate-500 w-10">{i + 1}</td>
                    <td className="px-3 py-2.5 font-mono text-xs text-slate-200">
                      {e.hostname}
                    </td>
                    <td className="px-3 py-2.5 text-xs text-slate-400">{e.detail}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
