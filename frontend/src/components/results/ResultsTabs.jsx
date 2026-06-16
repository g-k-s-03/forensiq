import { useState } from 'react'
import SummaryCards from './SummaryCards'
import TamperFlagsTable from './TamperFlagsTable'

function TabBtn({ label, active, badge, badgeRed, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
        active
          ? 'border-blue-500 text-white'
          : 'border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-600'
      }`}
    >
      {label}
      {badge != null && badge > 0 && (
        <span
          className={`inline-flex items-center justify-center min-w-[1.25rem] h-5 px-1.5 rounded-full text-xs font-bold ${
            badgeRed ? 'bg-red-600 text-white' : 'bg-slate-700 text-slate-300'
          }`}
        >
          {badge}
        </span>
      )}
    </button>
  )
}

function Placeholder({ text }) {
  return (
    <div className="flex items-center justify-center h-40 rounded-xl border border-dashed border-slate-700 text-slate-500 text-sm">
      {text}
    </div>
  )
}

export default function ResultsTabs({ results }) {
  const [active, setActive] = useState('overview')
  const s = results.summary ?? {}
  const flags = results.tamper_flags ?? []
  const hasHigh = (s.high_flags ?? 0) > 0

  const browserCount = (s.browser_history_live ?? 0) + (s.browser_history_recovered ?? 0)

  return (
    <div className="flex flex-col">
      {/* Tab bar */}
      <div className="flex border-b border-slate-700/60 overflow-x-auto">
        <TabBtn
          label="Overview"
          active={active === 'overview'}
          onClick={() => setActive('overview')}
        />
        <TabBtn
          label="Tamper Flags"
          active={active === 'tamper'}
          badge={s.tamper_flags}
          badgeRed={hasHigh}
          onClick={() => setActive('tamper')}
        />
        <TabBtn
          label="Browser Forensics"
          active={active === 'browser'}
          badge={browserCount}
          onClick={() => setActive('browser')}
        />
        <TabBtn
          label="Timeline"
          active={active === 'timeline'}
          badge={s.timeline_events}
          onClick={() => setActive('timeline')}
        />
      </div>

      {/* Tab content */}
      <div className="pt-5">
        {active === 'overview' && (
          <SummaryCards summary={s} tamperFlags={flags} />
        )}
        {active === 'tamper' && (
          <TamperFlagsTable flags={flags} />
        )}
        {active === 'browser' && (
          <Placeholder text="Browser Forensics — coming in F4" />
        )}
        {active === 'timeline' && (
          <Placeholder text="Timeline — coming in F4" />
        )}
      </div>
    </div>
  )
}
