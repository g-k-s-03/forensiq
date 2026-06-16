const fmtBytes = (bytes) => {
  if (!bytes || bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let val = bytes
  let i = 0
  while (val >= 1024 && i < units.length - 1) {
    val /= 1024
    i++
  }
  return `${val.toFixed(1)} ${units[i]}`
}

const dangerBadge = (type) => {
  if (type === 0)  return { label: 'SAFE',      cls: 'bg-green-900/70 text-green-300 border border-green-700/40' }
  if (type === 3)  return { label: 'DANGEROUS', cls: 'bg-red-900/70 text-red-300 border border-red-700/40' }
  return { label: 'UNKNOWN', cls: 'bg-yellow-900/70 text-yellow-300 border border-yellow-700/40' }
}

const trunc = (s = '', n) => (s.length <= n ? s : s.slice(0, n - 1) + '…')

const SRC_BADGE = {
  'Chrome/Edge': 'bg-blue-900/70 text-blue-300',
  'Firefox':     'bg-orange-900/70 text-orange-300',
}

export default function DownloadsTable({ downloads = [] }) {
  if (downloads.length === 0) {
    return (
      <p className="text-center text-slate-500 text-xs py-8">No downloads found.</p>
    )
  }

  return (
    <div className="rounded-lg border border-slate-700 overflow-hidden">
      <div className="max-h-96 overflow-y-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-700 sticky top-0 z-10">
              {['#', 'Source', 'File / URL', 'Size', 'Start Time', 'Danger'].map((h) => (
                <th
                  key={h}
                  className="px-3 py-2.5 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider whitespace-nowrap"
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/80">
            {downloads.map((d, i) => {
              const path   = d.target_path || d.url || ''
              const danger = dangerBadge(d.danger_type)
              return (
                <tr
                  key={i}
                  className={`transition-colors hover:bg-slate-700/40 ${
                    i % 2 === 0 ? 'bg-slate-800/40' : 'bg-slate-800/70'
                  }`}
                >
                  <td className="px-3 py-2.5 text-xs text-slate-500 w-10">{i + 1}</td>

                  <td className="px-3 py-2.5 w-28">
                    <span
                      className={`text-xs px-1.5 py-0.5 rounded font-medium ${
                        SRC_BADGE[d.source] ?? 'bg-slate-700 text-slate-300'
                      }`}
                    >
                      {d.source}
                    </span>
                  </td>

                  <td className="px-3 py-2.5 max-w-xs">
                    <span
                      className="font-mono text-xs text-slate-200 block truncate max-w-[16rem]"
                      title={path}
                    >
                      {trunc(path, 60)}
                    </span>
                  </td>

                  <td className="px-3 py-2.5 text-xs font-mono text-slate-400 w-24 whitespace-nowrap">
                    {fmtBytes(d.total_bytes)}
                  </td>

                  <td className="px-3 py-2.5 text-xs font-mono text-slate-400 w-36 whitespace-nowrap">
                    {d.start_time || '—'}
                  </td>

                  <td className="px-3 py-2.5 w-28">
                    <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${danger.cls}`}>
                      {danger.label}
                    </span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
