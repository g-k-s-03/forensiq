import { useMemo } from 'react'
import { FileSearch } from 'lucide-react'
import Badge from '../ui/Badge'
import Table from '../ui/Table'

function shortHash(sha256) {
  if (!sha256) return '—'
  return sha256.slice(0, 16) + '…'
}

export default function FileInventoryTable({ files = [], tamperFlags = [] }) {
  const flaggedPaths = useMemo(() => {
    const s = new Set()
    tamperFlags.forEach((f) => {
      if (f.file) s.add(f.file)
    })
    return s
  }, [tamperFlags])

  const columns = [
    { key: '_idx', label: '#', width: '3rem', render: (_, __, i) => (
      <span className="text-slate-500">{i + 1}</span>
    )},
    { key: 'name', label: 'File Name', render: (v, row) => (
      <span className="font-mono text-slate-200" title={row.rel_path}>{v}</span>
    )},
    { key: 'extension', label: 'Ext', width: '4rem', render: (v) => (
      v ? <Badge color="slate">{v}</Badge> : <span className="text-slate-600">—</span>
    )},
    { key: 'size_human', label: 'Size', width: '6rem', render: (v) => (
      <span className="text-slate-400">{v || '—'}</span>
    )},
    { key: 'created', label: 'Created', width: '12rem', render: (v) => (
      <span className="font-mono text-slate-400 text-xs">{v || '—'}</span>
    )},
    { key: 'modified', label: 'Modified', width: '12rem', render: (v) => (
      <span className="font-mono text-slate-400 text-xs">{v || '—'}</span>
    )},
    { key: 'sha256', label: 'SHA-256', render: (v) => (
      <span className="font-mono text-slate-500 text-xs" title={v}>{shortHash(v)}</span>
    )},
    { key: '_flags', label: 'Flags', width: '5rem', render: (_, row) => {
      const count = tamperFlags.filter(
        (f) => f.file === row.rel_path || f.file === row.name
      ).length
      return count > 0
        ? <Badge color="red">{count} flag{count > 1 ? 's' : ''}</Badge>
        : <span className="text-slate-600 text-xs">—</span>
    }},
  ]

  // Inject index into each row and fix render signature
  const normalizedCols = columns.map((col) =>
    col.key === '_idx' || col.key === '_flags'
      ? col
      : col
  )

  const rows = files

  if (files.length === 0) {
    return (
      <div className="flex flex-col items-center gap-3 py-12 text-slate-500">
        <FileSearch size={32} className="text-slate-700" />
        <p className="text-sm">No file metadata available.</p>
        <p className="text-xs text-slate-600">
          Re-run the analysis to populate the file inventory.
        </p>
      </div>
    )
  }

  // Build columns with index-aware render for '#'
  const finalColumns = [
    { key: '_idx', label: '#', width: '3rem' },
    { key: 'name', label: 'File Name', render: (v, row) => (
      <span className="font-mono text-slate-200" title={row.rel_path}>{v}</span>
    )},
    { key: 'extension', label: 'Ext', width: '4rem', render: (v) => (
      v ? <Badge color="slate">{v}</Badge> : <span className="text-slate-600">—</span>
    )},
    { key: 'size_human', label: 'Size', width: '6rem', render: (v) => (
      <span className="text-slate-400">{v || '—'}</span>
    )},
    { key: 'created', label: 'Created', width: '12rem', render: (v) => (
      <span className="font-mono text-slate-400 text-xs">{v || '—'}</span>
    )},
    { key: 'modified', label: 'Modified', width: '12rem', render: (v) => (
      <span className="font-mono text-slate-400 text-xs">{v || '—'}</span>
    )},
    { key: 'sha256', label: 'SHA-256', render: (v) => (
      <span className="font-mono text-slate-500 text-xs" title={v || ''}>{shortHash(v)}</span>
    )},
    { key: '_flags', label: 'Flags', width: '5rem' },
  ]

  return (
    <div className="flex flex-col gap-3">
      <p className="text-xs text-slate-500">{files.length} file{files.length !== 1 ? 's' : ''} in evidence directory</p>
      <div className="rounded-lg border border-slate-700 overflow-hidden">
        <div className="max-h-[32rem] overflow-y-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-700 sticky top-0 z-10">
                {finalColumns.map((col) => (
                  <th
                    key={col.key}
                    className="px-3 py-2.5 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider whitespace-nowrap"
                    style={col.width ? { width: col.width } : {}}
                  >
                    {col.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {files.map((row, i) => {
                const isFlagged = flaggedPaths.has(row.rel_path) || flaggedPaths.has(row.name)
                const flagCount = tamperFlags.filter(
                  (f) => f.file === row.rel_path || f.file === row.name
                ).length
                return (
                  <tr
                    key={i}
                    className={`transition-colors hover:bg-slate-700/40 ${
                      isFlagged
                        ? 'bg-red-950/30'
                        : i % 2 === 0
                        ? 'bg-slate-800/40'
                        : 'bg-slate-800/70'
                    }`}
                  >
                    <td className="px-3 py-2.5 text-xs text-slate-500 w-12">{i + 1}</td>
                    <td className="px-3 py-2.5 text-xs">
                      <span className="font-mono text-slate-200" title={row.rel_path}>{row.name}</span>
                    </td>
                    <td className="px-3 py-2.5 text-xs">
                      {row.extension ? <Badge color="slate">{row.extension}</Badge> : <span className="text-slate-600">—</span>}
                    </td>
                    <td className="px-3 py-2.5 text-xs text-slate-400">{row.size_human || '—'}</td>
                    <td className="px-3 py-2.5 text-xs font-mono text-slate-400">{row.created || '—'}</td>
                    <td className="px-3 py-2.5 text-xs font-mono text-slate-400">{row.modified || '—'}</td>
                    <td className="px-3 py-2.5 text-xs">
                      <span className="font-mono text-slate-500" title={row.sha256 || ''}>{shortHash(row.sha256)}</span>
                    </td>
                    <td className="px-3 py-2.5 text-xs">
                      {flagCount > 0
                        ? <Badge color="red">{flagCount} flag{flagCount > 1 ? 's' : ''}</Badge>
                        : <span className="text-slate-600">—</span>}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
