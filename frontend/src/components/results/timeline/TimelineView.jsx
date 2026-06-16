import { Fragment, useMemo, useState } from 'react'
import { Search, LayoutList, GitCommitVertical } from 'lucide-react'

const UNKNOWN_TS = '0000-00-00 00:00:00'
const CHUNK = 50

const CONF_BADGE = {
  CONFIRMED: 'bg-green-900/70 text-green-300 border border-green-700/40',
  INFERRED:  'bg-yellow-900/70 text-yellow-300 border border-yellow-700/40',
  RECOVERED: 'bg-cyan-900/70 text-cyan-300 border border-cyan-700/40',
}
const CONF_BORDER = {
  CONFIRMED: 'border-green-500',
  INFERRED:  'border-yellow-500',
  RECOVERED: 'border-cyan-500',
}
const CONF_DOT = {
  CONFIRMED: 'bg-green-500',
  INFERRED:  'bg-yellow-500',
  RECOVERED: 'bg-cyan-500',
}

const inputCls =
  'rounded bg-slate-900 border border-slate-700 text-slate-200 placeholder-slate-500 px-2.5 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-transparent'
const selectCls =
  'rounded bg-slate-900 border border-slate-700 text-slate-200 px-2.5 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer'

const EVENT_TYPES = [
  'FILE_CREATED', 'FILE_MODIFIED', 'BROWSER_VISIT',
  'BROWSER_DOWNLOAD', 'BROWSER_COOKIE', 'DNS_LOOKUP', 'BROWSER_EXECUTED',
]
const SOURCES = [
  'File System', 'Chrome/Edge', 'Firefox', 'Freelist Recovery', 'DNS Cache', 'Prefetch',
]

/* ── Table mode ────────────────────────────────────────────────────────────── */
function TableView({ events }) {
  const [visible, setVisible] = useState(CHUNK)
  const shown   = events.slice(0, visible)
  const hasMore = events.length > visible

  return (
    <div className="flex flex-col gap-2">
      <div className="rounded-lg border border-slate-700 overflow-hidden">
        <div className="max-h-[32rem] overflow-y-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-700 sticky top-0 z-10">
                {['Timestamp', 'Source', 'Event Type', 'Confidence', 'Description'].map((h) => (
                  <th key={h} className="px-3 py-2.5 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider whitespace-nowrap">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {shown.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-slate-500 text-xs">
                    No events match the current filters.
                  </td>
                </tr>
              ) : (
                shown.map((ev, i) => {
                  const isUnknown = ev.timestamp === UNKNOWN_TS
                  return (
                    <tr
                      key={i}
                      className={`transition-colors hover:bg-slate-700/40 ${
                        ev.confidence === 'RECOVERED'
                          ? 'bg-cyan-950/30'
                          : i % 2 === 0
                          ? 'bg-slate-800/40'
                          : 'bg-slate-800/70'
                      }`}
                    >
                      <td className="px-3 py-2.5 text-xs font-mono text-slate-400 whitespace-nowrap w-40">
                        {isUnknown ? <span className="text-slate-600 italic">Unknown</span> : ev.timestamp}
                      </td>
                      <td className="px-3 py-2.5 text-xs text-slate-400 whitespace-nowrap w-32">
                        {ev.source}
                      </td>
                      <td className="px-3 py-2.5 w-40">
                        <span className="text-xs font-mono bg-slate-700 text-slate-300 px-1.5 py-0.5 rounded whitespace-nowrap">
                          {ev.event_type}
                        </span>
                      </td>
                      <td className="px-3 py-2.5 w-28">
                        <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${CONF_BADGE[ev.confidence] ?? 'bg-slate-700 text-slate-300'}`}>
                          {ev.confidence}
                        </span>
                      </td>
                      <td className="px-3 py-2.5 text-xs text-slate-300 max-w-xs">
                        <span className="line-clamp-2" title={ev.description}>{ev.description}</span>
                      </td>
                    </tr>
                  )
                })
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
          Load {Math.min(CHUNK, events.length - visible)} more events…
        </button>
      )}
    </div>
  )
}

/* ── Visual mode ───────────────────────────────────────────────────────────── */
function VisualView({ events }) {
  const capped   = events.slice(0, 50)
  const overflow = events.length > 50

  return (
    <div className="flex flex-col gap-2">
      {overflow && (
        <p className="text-xs text-slate-500 text-center py-1">
          Showing first 50 events. Switch to table view for all {events.length} events.
        </p>
      )}

      <div className="grid" style={{ gridTemplateColumns: '7rem 1.5rem 1fr' }}>
        {capped.map((ev, i) => {
          const isLast    = i === capped.length - 1
          const isUnknown = ev.timestamp === UNKNOWN_TS
          const [date, time] = isUnknown ? ['', ''] : ev.timestamp.split(' ')

          return (
            <Fragment key={i}>
              {/* Timestamp */}
              <div className="text-right pr-3 pt-2 pb-3 flex-shrink-0">
                {isUnknown ? (
                  <span className="text-xs font-mono text-slate-600 italic">Unknown</span>
                ) : (
                  <>
                    <div className="text-xs font-mono text-slate-400 leading-tight">{date}</div>
                    <div className="text-xs font-mono text-slate-500 leading-tight">{time}</div>
                  </>
                )}
              </div>

              {/* Dot + connecting line */}
              <div className="flex flex-col items-center">
                <div className={`w-2.5 h-2.5 rounded-full ring-2 ring-slate-900 mt-2.5 flex-shrink-0 ${CONF_DOT[ev.confidence] ?? 'bg-slate-500'}`} />
                {!isLast && (
                  <div className="w-px flex-1 bg-slate-700/60 min-h-[1.5rem] my-0.5" />
                )}
              </div>

              {/* Card */}
              <div className="pl-3 pb-3 min-w-0">
                <div className={`border-l-2 ${CONF_BORDER[ev.confidence] ?? 'border-slate-600'} rounded-r-lg bg-slate-800/60 px-3 py-2.5`}>
                  <div className="flex flex-wrap items-center gap-1.5 mb-1">
                    <span className="text-xs font-mono bg-slate-700 text-slate-300 px-1.5 py-0.5 rounded">
                      {ev.event_type}
                    </span>
                    <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${CONF_BADGE[ev.confidence] ?? 'bg-slate-700 text-slate-300'}`}>
                      {ev.confidence}
                    </span>
                    <span className="text-xs text-slate-500">{ev.source}</span>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed break-words">{ev.description}</p>
                </div>
              </div>
            </Fragment>
          )
        })}
      </div>

      {events.length === 0 && (
        <p className="text-center text-slate-500 text-xs py-8">
          No events match the current filters.
        </p>
      )}
    </div>
  )
}

/* ── Main component ─────────────────────────────────────────────────────────── */
export default function TimelineView({ timeline = [] }) {
  const [search, setSearch]    = useState('')
  const [confidence, setConf]  = useState('all')
  const [eventType, setEvType] = useState('all')
  const [sourceFilter, setSrc] = useState('all')
  const [mode, setMode]        = useState('table')

  const filtered = useMemo(() => timeline.filter((ev) => {
    const q = search.toLowerCase()
    const matchSearch = !q || ev.description?.toLowerCase().includes(q) || ev.source?.toLowerCase().includes(q)
    const matchConf   = confidence === 'all' || ev.confidence === confidence
    const matchType   = eventType  === 'all' || ev.event_type === eventType
    const matchSrc    = sourceFilter === 'all' || ev.source === sourceFilter
    return matchSearch && matchConf && matchType && matchSrc
  }), [timeline, search, confidence, eventType, sourceFilter])

  return (
    <div className="flex flex-col gap-4">
      {/* Controls bar */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative">
          <Search size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none" />
          <input
            className={inputCls + ' pl-7 w-48'}
            placeholder="Search events…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <select className={selectCls} value={confidence} onChange={(e) => setConf(e.target.value)}>
          <option value="all">All Confidence</option>
          <option value="CONFIRMED">CONFIRMED</option>
          <option value="INFERRED">INFERRED</option>
          <option value="RECOVERED">RECOVERED</option>
        </select>

        <select className={selectCls} value={eventType} onChange={(e) => setEvType(e.target.value)}>
          <option value="all">All Event Types</option>
          {EVENT_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>

        <select className={selectCls} value={sourceFilter} onChange={(e) => setSrc(e.target.value)}>
          <option value="all">All Sources</option>
          {SOURCES.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>

        <div className="ml-auto flex items-center gap-3">
          <span className="text-xs text-slate-500">
            Showing {filtered.length} of {timeline.length} events
          </span>
          <div className="flex rounded-lg border border-slate-700 overflow-hidden">
            <button
              onClick={() => setMode('table')}
              title="Table view"
              className={`flex items-center gap-1.5 px-2.5 py-1.5 text-xs transition-colors ${
                mode === 'table' ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              <LayoutList size={13} /> Table
            </button>
            <button
              onClick={() => setMode('visual')}
              title="Visual timeline"
              className={`flex items-center gap-1.5 px-2.5 py-1.5 text-xs border-l border-slate-700 transition-colors ${
                mode === 'visual' ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              <GitCommitVertical size={13} /> Visual
            </button>
          </div>
        </div>
      </div>

      {mode === 'table'  && <TableView  events={filtered} />}
      {mode === 'visual' && <VisualView events={filtered} />}
    </div>
  )
}
