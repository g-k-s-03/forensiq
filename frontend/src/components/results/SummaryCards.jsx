import {
  Folder,
  ShieldAlert,
  Globe,
  Download,
  Clock,
  EyeOff,
  AlertTriangle,
  FileX,
} from 'lucide-react'

const borderFor = (cond) =>
  cond === 'red'
    ? 'border-red-500/50'
    : cond === 'yellow'
    ? 'border-yellow-500/50'
    : cond === 'green'
    ? 'border-green-500/40'
    : 'border-slate-700/50'

const accentFor = (cond) =>
  cond === 'red'
    ? 'text-red-400'
    : cond === 'yellow'
    ? 'text-yellow-400'
    : cond === 'green'
    ? 'text-green-400'
    : 'text-slate-100'

function MetricCard({ icon: Icon, label, value, subtext, border = '', accent = '' }) {
  return (
    <div
      className={`flex flex-col gap-1 rounded-xl bg-slate-800/60 border px-5 py-4 ${
        border || 'border-slate-700/50'
      }`}
    >
      <div className="flex items-center gap-2 text-slate-400 text-xs uppercase tracking-wider font-medium">
        <Icon size={13} />
        {label}
      </div>
      <div className={`text-2xl font-bold font-mono mt-1 ${accent || 'text-slate-100'}`}>
        {value}
      </div>
      {subtext && (
        <div className="text-xs text-slate-500 mt-0.5 leading-relaxed">{subtext}</div>
      )}
    </div>
  )
}

export default function SummaryCards({ summary, tamperFlags = [] }) {
  const s = summary ?? {}

  const antiForensic = tamperFlags.filter((f) => f.type === 'ANTI_FORENSIC').length
  const disguised    = tamperFlags.filter((f) => f.type === 'DISGUISED_FILE').length

  const flagBorder =
    (s.high_flags ?? 0) > 0
      ? 'red'
      : (s.medium_flags ?? 0) > 0
      ? 'yellow'
      : (s.tamper_flags ?? 0) === 0
      ? 'green'
      : ''

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      <MetricCard
        icon={Folder}
        label="Files Scanned"
        value={s.files_scanned ?? 0}
      />

      <MetricCard
        icon={ShieldAlert}
        label="Tamper Flags"
        value={s.tamper_flags ?? 0}
        subtext={`${s.high_flags ?? 0} HIGH / ${s.medium_flags ?? 0} MEDIUM / ${s.low_flags ?? 0} LOW`}
        border={borderFor(flagBorder)}
        accent={accentFor(flagBorder)}
      />

      <MetricCard
        icon={Globe}
        label="Browser History"
        value={s.browser_history_live ?? 0}
        subtext={`+ ${s.browser_history_recovered ?? 0} recovered`}
      />

      <MetricCard
        icon={Download}
        label="Downloads"
        value={s.downloads ?? 0}
      />

      <MetricCard
        icon={Clock}
        label="Timeline Events"
        value={s.timeline_events ?? 0}
        subtext={`${s.confirmed_events ?? 0} confirmed / ${s.inferred_events ?? 0} inferred`}
      />

      <MetricCard
        icon={EyeOff}
        label="Hidden Files"
        value={s.hidden_files ?? 0}
        accent={(s.hidden_files ?? 0) > 0 ? 'text-yellow-400' : ''}
      />

      <MetricCard
        icon={AlertTriangle}
        label="Anti-Forensic"
        value={antiForensic}
        border={antiForensic > 0 ? borderFor('red') : ''}
        accent={antiForensic > 0 ? accentFor('red') : ''}
      />

      <MetricCard
        icon={FileX}
        label="Disguised Files"
        value={disguised}
        border={disguised > 0 ? borderFor('red') : ''}
        accent={disguised > 0 ? accentFor('red') : ''}
      />
    </div>
  )
}
