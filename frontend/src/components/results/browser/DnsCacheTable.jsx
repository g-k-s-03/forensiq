import { Info } from 'lucide-react'
import Table from '../../ui/Table'

const COLUMNS = [
  { key: '_idx', label: '#', width: '3rem' },
  { key: 'hostname', label: 'Hostname', render: (v) => (
    <span className="font-mono text-xs text-slate-200">{v}</span>
  )},
  { key: 'detail', label: 'Detail', render: (v) => (
    <span className="text-xs text-slate-400">{v || '—'}</span>
  )},
]

export default function DnsCacheTable({ dnsCcache = [] }) {
  const rows = dnsCcache.map((e, i) => ({ ...e, _idx: i + 1 }))

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-start gap-2 rounded-lg border border-yellow-500/30 bg-yellow-500/10 px-4 py-3 text-xs text-yellow-400">
        <Info size={13} className="mt-0.5 shrink-0" />
        <span>
          DNS cache entries reflect hostnames resolved on the examined machine at time of
          analysis. These are <strong>INFERRED</strong> artifacts and do not constitute
          confirmed browsing activity.
        </span>
      </div>

      <Table
        columns={COLUMNS}
        rows={rows}
        emptyMessage="No DNS cache entries found."
        rowClass={(row, i) =>
          i % 2 === 0 ? 'bg-slate-800/40' : 'bg-slate-800/70'
        }
      />
    </div>
  )
}
