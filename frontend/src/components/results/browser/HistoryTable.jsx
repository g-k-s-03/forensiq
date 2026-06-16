import { useMemo, useState } from 'react'
import { Search, ExternalLink } from 'lucide-react'
import Badge from '../../ui/Badge'

const SRC_COLOR = { 'Chrome/Edge': 'blue', 'Firefox': 'orange', 'Freelist Recovery': 'cyan' }

const inputCls =
  'rounded bg-slate-900 border border-slate-700 text-slate-200 placeholder-slate-500 px-2.5 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-transparent'
const selectCls =
  'rounded bg-slate-900 border border-slate-700 text-slate-200 px-2.5 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer'

const CHUNK = 50

export default function HistoryTable({ history = [] }) {
  const [search, setSearch]           = useState('')
  const [sourceFilter, setSource]     = useState('all')
  const [recoveredOnly, setRecovered] = useState(false)
  const [visible, setVisible]         = useState(CHUNK)

  const filtered = useMemo(() => history.filter((r) => {
    const q = search.toLowerCase()
    const matchSearch = !q || r.url?.toLowerCase().includes(q) || r.title?.toLowerCase().includes(q)
    const matchSource = sourceFilter === 'all' || r.source === sourceFilter
    const matchRec    = !recoveredOnly || r.recovered
    return matchSearch && matchSource && matchRec
  }), [history, search, sourceFilter, recoveredOnly])

  const shown   = filtered.slice(0, visible)
  const hasMore = filtered.length > visible

  return (
    <div className="flex flex-col gap-3">
      {/* Filter bar */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative">
          <Search size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none" />
          <input
            className={inputCls + ' pl-7 w-52'}
            placeholder="Search URL or title…"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setVisible(CHUNK) }}
          />
        </div>

        <select className={selectCls} value={sourceFilter} onChange={(e) => { setSource(e.target.value); setVisible(CHUNK) }}>
          <option value="all">All Sources</option>
          <option value="Chrome/Edge">Chrome/Edge</option>
          <option value="Firefox">Firefox</option>
          <option value="Freelist Recovery">Freelist Recovery</option>
        </select>

        <label className="flex items-center gap-2 text-xs text-slate-400 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={recoveredOnly}
            onChange={(e) => { setRecovered(e.target.checked); setVisible(CHUNK) }}
            className="rounded border-slate-600 bg-slate-900 accent-blue-500"
          />
          Recovered Only
        </label>

        <span className="ml-auto text-xs text-slate-500">
          Showing {Math.min(visible, filtered.length)} of {filtered.length} records
        </span>
      </div>

      {/* Table */}
      <div className="rounded-lg border border-slate-700 overflow-hidden">
        <div className="max-h-96 overflow-y-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-700 sticky top-0 z-10">
                {['#', 'Source', 'URL', 'Title', 'Last Visit', 'Visits', 'Status'].map((h) => (
                  <th key={h} className="px-3 py-2.5 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider whitespace-nowrap">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {shown.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-slate-500 text-xs">
                    No browser history found.
                  </td>
                </tr>
              ) : (
                shown.map((r, i) => (
                  <tr
                    key={i}
                    className={`transition-colors hover:bg-slate-700/40 ${
                      r.recovered ? 'bg-cyan-950/40' : i % 2 === 0 ? 'bg-slate-800/40' : 'bg-slate-800/70'
                    }`}
                  >
                    <td className="px-3 py-2.5 text-xs text-slate-500 w-10">{i + 1}</td>
                    <td className="px-3 py-2.5 w-32">
                      <Badge color={SRC_COLOR[r.source] ?? 'slate'}>{r.source}</Badge>
                    </td>
                    <td className="px-3 py-2.5 max-w-[14rem]">
                      {r.url ? (
                        <a
                          href={r.url}
                          target="_blank"
                          rel="noreferrer"
                          title={r.url}
                          className="flex items-center gap-1 font-mono text-xs text-blue-400 hover:text-blue-300 max-w-[13rem] truncate"
                        >
                          <span className="truncate">{r.url.length > 60 ? r.url.slice(0, 59) + '…' : r.url}</span>
                          <ExternalLink size={10} className="shrink-0" />
                        </a>
                      ) : (
                        <span className="text-slate-500">—</span>
                      )}
                    </td>
                    <td className="px-3 py-2.5 text-xs text-slate-300 max-w-[10rem] truncate" title={r.title}>
                      {r.title || <span className="text-slate-500">—</span>}
                    </td>
                    <td className="px-3 py-2.5 text-xs font-mono text-slate-400 whitespace-nowrap w-36">
                      {r.last_visit_time || '—'}
                    </td>
                    <td className="px-3 py-2.5 text-xs text-slate-300 text-center w-14">
                      {r.visit_count ?? '—'}
                    </td>
                    <td className="px-3 py-2.5 w-24">
                      <Badge color={r.recovered ? 'cyan' : 'green'}>
                        {r.recovered ? 'RECOVERED' : 'LIVE'}
                      </Badge>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {hasMore && (
        <button
          onClick={() => setVisible((v) => v + CHUNK)}
          className="self-center text-xs text-blue-400 hover:text-blue-300 transition-colors py-1"
        >
          Load {Math.min(CHUNK, filtered.length - visible)} more records…
        </button>
      )}
    </div>
  )
}
