import { useState } from 'react'
import { Search, ExternalLink } from 'lucide-react'

const SRC_BADGE = {
  'Chrome/Edge':       'bg-blue-900/70 text-blue-300 border border-blue-700/40',
  'Firefox':           'bg-orange-900/70 text-orange-300 border border-orange-700/40',
  'Freelist Recovery': 'bg-cyan-900/70 text-cyan-300 border border-cyan-700/40',
}

const inputCls =
  'rounded bg-slate-900 border border-slate-700 text-slate-200 placeholder-slate-500 px-2.5 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-transparent'
const selectCls =
  'rounded bg-slate-900 border border-slate-700 text-slate-200 px-2.5 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer'

const trunc = (s = '', n) => (s.length <= n ? s : s.slice(0, n - 1) + '…')

export default function HistoryTable({ history = [] }) {
  const [search, setSearch]           = useState('')
  const [sourceFilter, setSource]     = useState('all')
  const [recoveredOnly, setRecovered] = useState(false)

  const filtered = history.filter((r) => {
    const q = search.toLowerCase()
    const matchSearch =
      !q ||
      r.url?.toLowerCase().includes(q) ||
      r.title?.toLowerCase().includes(q)
    const matchSource = sourceFilter === 'all' || r.source === sourceFilter
    const matchRec    = !recoveredOnly || r.recovered
    return matchSearch && matchSource && matchRec
  })

  return (
    <div className="flex flex-col gap-3">
      {/* Filter bar */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative">
          <Search
            size={12}
            className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none"
          />
          <input
            className={inputCls + ' pl-7 w-52'}
            placeholder="Search URL or title…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <select
          className={selectCls}
          value={sourceFilter}
          onChange={(e) => setSource(e.target.value)}
        >
          <option value="all">All Sources</option>
          <option value="Chrome/Edge">Chrome/Edge</option>
          <option value="Firefox">Firefox</option>
          <option value="Freelist Recovery">Freelist Recovery</option>
        </select>

        <label className="flex items-center gap-2 text-xs text-slate-400 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={recoveredOnly}
            onChange={(e) => setRecovered(e.target.checked)}
            className="rounded border-slate-600 bg-slate-900 accent-blue-500"
          />
          Recovered Only
        </label>

        <span className="ml-auto text-xs text-slate-500">
          Showing {filtered.length} of {history.length} records
        </span>
      </div>

      {/* Table */}
      <div className="rounded-lg border border-slate-700 overflow-hidden">
        <div className="max-h-96 overflow-y-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-700 sticky top-0 z-10">
                {['#', 'Source', 'URL', 'Title', 'Last Visit', 'Visits', 'Status'].map((h) => (
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
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-slate-500 text-xs">
                    No browser history found.
                  </td>
                </tr>
              ) : (
                filtered.map((r, i) => (
                  <tr
                    key={i}
                    className={`transition-colors hover:bg-slate-700/40 ${
                      r.recovered
                        ? 'bg-cyan-950/40'
                        : i % 2 === 0
                        ? 'bg-slate-800/40'
                        : 'bg-slate-800/70'
                    }`}
                  >
                    <td className="px-3 py-2.5 text-xs text-slate-500 w-10">{i + 1}</td>

                    <td className="px-3 py-2.5 w-32">
                      <span
                        className={`text-xs px-1.5 py-0.5 rounded font-medium whitespace-nowrap ${
                          SRC_BADGE[r.source] ?? 'bg-slate-700 text-slate-300'
                        }`}
                      >
                        {r.source}
                      </span>
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
                          <span className="truncate">{trunc(r.url, 60)}</span>
                          <ExternalLink size={10} className="shrink-0" />
                        </a>
                      ) : (
                        <span className="text-slate-500">—</span>
                      )}
                    </td>

                    <td
                      className="px-3 py-2.5 text-xs text-slate-300 max-w-[10rem] truncate"
                      title={r.title}
                    >
                      {r.title || <span className="text-slate-500">—</span>}
                    </td>

                    <td className="px-3 py-2.5 text-xs font-mono text-slate-400 whitespace-nowrap w-36">
                      {r.last_visit_time || '—'}
                    </td>

                    <td className="px-3 py-2.5 text-xs text-slate-300 text-center w-14">
                      {r.visit_count ?? '—'}
                    </td>

                    <td className="px-3 py-2.5 w-24">
                      {r.recovered ? (
                        <span className="text-xs px-1.5 py-0.5 rounded bg-cyan-900/70 text-cyan-300 border border-cyan-700/40 font-medium">
                          RECOVERED
                        </span>
                      ) : (
                        <span className="text-xs px-1.5 py-0.5 rounded bg-green-900/70 text-green-300 border border-green-700/40 font-medium">
                          LIVE
                        </span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
