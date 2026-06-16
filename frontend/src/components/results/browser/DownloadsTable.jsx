import Badge from '../../ui/Badge'

const fmtBytes = (bytes) => {
  if (!bytes || bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let val = bytes, i = 0
  while (val >= 1024 && i < units.length - 1) { val /= 1024; i++ }
  return `${val.toFixed(1)} ${units[i]}`
}

const SRC_COLOR   = { 'Chrome/Edge': 'blue', 'Firefox': 'orange' }
const dangerColor = (type) => {
  if (type === 0) return { color: 'green',  label: 'SAFE' }
  if (type === 3) return { color: 'red',    label: 'DANGEROUS' }
  return              { color: 'yellow', label: 'UNKNOWN' }
}

export default function DownloadsTable({ downloads = [] }) {
  if (downloads.length === 0) {
    return <p className="text-center text-slate-500 text-xs py-8">No downloads found.</p>
  }

  return (
    <div className="rounded-lg border border-slate-700 overflow-hidden">
      <div className="max-h-96 overflow-y-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-700 sticky top-0 z-10">
              {['#', 'Source', 'File / URL', 'Size', 'Start Time', 'Danger'].map((h) => (
                <th key={h} className="px-3 py-2.5 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider whitespace-nowrap">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/80">
            {downloads.map((d, i) => {
              const path = d.target_path || d.url || ''
              const { color, label } = dangerColor(d.danger_type)
              return (
                <tr key={i} className={`transition-colors hover:bg-slate-700/40 ${i % 2 === 0 ? 'bg-slate-800/40' : 'bg-slate-800/70'}`}>
                  <td className="px-3 py-2.5 text-xs text-slate-500 w-10">{i + 1}</td>
                  <td className="px-3 py-2.5 w-28">
                    <Badge color={SRC_COLOR[d.source] ?? 'slate'}>{d.source}</Badge>
                  </td>
                  <td className="px-3 py-2.5 max-w-xs">
                    <span className="font-mono text-xs text-slate-200 block truncate max-w-[16rem]" title={path}>
                      {path.length > 60 ? path.slice(0, 59) + '…' : path}
                    </span>
                  </td>
                  <td className="px-3 py-2.5 text-xs font-mono text-slate-400 w-24 whitespace-nowrap">
                    {fmtBytes(d.total_bytes)}
                  </td>
                  <td className="px-3 py-2.5 text-xs font-mono text-slate-400 w-36 whitespace-nowrap">
                    {d.start_time || '—'}
                  </td>
                  <td className="px-3 py-2.5 w-28">
                    <Badge color={color}>{label}</Badge>
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
