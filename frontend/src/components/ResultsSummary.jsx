import {
  CheckCircle,
  FileText,
  ShieldAlert,
  Clock,
  Download,
  RotateCcw,
} from 'lucide-react'
import { getPdfUrl, getJsonUrl } from '../api/client'

const Stat = ({ icon: Icon, label, value, accent }) => (
  <div className="flex flex-col gap-1 rounded-xl bg-slate-800/60 border border-slate-700/50 px-5 py-4">
    <div className="flex items-center gap-2 text-slate-400 text-xs uppercase tracking-wider">
      <Icon size={13} />
      {label}
    </div>
    <div className={`text-2xl font-bold font-mono ${accent ?? 'text-slate-100'}`}>
      {value}
    </div>
  </div>
)

const Badge = ({ value, color }) => (
  <span className={`inline-block rounded px-2 py-0.5 text-xs font-mono font-semibold ${color}`}>
    {value}
  </span>
)

export default function ResultsSummary({ results, onReset }) {
  const s = results.summary ?? {}
  const files = results.output_files ?? {}

  const highFlags   = s.high_flags   ?? 0
  const medFlags    = s.medium_flags  ?? 0
  const lowFlags    = s.low_flags    ?? 0
  const totalFlags  = s.tamper_flags ?? 0

  return (
    <div className="flex flex-col gap-6">
      {/* Banner */}
      <div className="flex items-center gap-3 rounded-xl border border-green-500/30 bg-green-500/10 px-5 py-4">
        <CheckCircle size={20} className="text-green-400 shrink-0" />
        <div>
          <p className="font-semibold text-green-300">Analysis Complete</p>
          <p className="text-xs text-slate-400 mt-0.5">
            Case <span className="font-mono text-slate-200">{results.case_id}</span>
            {' · '}{results.analysis_time}
          </p>
        </div>
      </div>

      {/* Key stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Stat icon={FileText} label="Files Scanned" value={s.files_scanned ?? 0} />
        <Stat
          icon={ShieldAlert}
          label="Tamper Flags"
          value={totalFlags}
          accent={totalFlags > 0 ? 'text-red-400' : 'text-green-400'}
        />
        <Stat icon={Clock} label="Timeline Events" value={s.timeline_events ?? 0} />
        <Stat
          icon={FileText}
          label="Browser Records"
          value={(s.browser_history_live ?? 0) + (s.browser_history_recovered ?? 0)}
        />
      </div>

      {/* Tamper breakdown */}
      {totalFlags > 0 && (
        <div className="rounded-xl border border-slate-700/50 bg-slate-800/40 px-5 py-4">
          <p className="text-xs uppercase tracking-wider text-slate-400 mb-3">
            Tamper Flag Breakdown
          </p>
          <div className="flex flex-wrap gap-2">
            <Badge value={`${highFlags} HIGH`}   color="bg-red-500/20 text-red-400" />
            <Badge value={`${medFlags} MEDIUM`}  color="bg-yellow-500/20 text-yellow-400" />
            <Badge value={`${lowFlags} LOW`}     color="bg-cyan-500/20 text-cyan-400" />
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            {(results.tamper_flags ?? []).slice(0, 8).map((f, i) => (
              <span
                key={i}
                className="text-xs font-mono bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-300"
              >
                {f.type}
              </span>
            ))}
            {(results.tamper_flags ?? []).length > 8 && (
              <span className="text-xs text-slate-500 px-2 py-1">
                +{results.tamper_flags.length - 8} more
              </span>
            )}
          </div>
        </div>
      )}

      {/* Downloads */}
      {(files.pdf || files.json) && (
        <div className="rounded-xl border border-slate-700/50 bg-slate-800/40 px-5 py-4">
          <p className="text-xs uppercase tracking-wider text-slate-400 mb-3">
            Output Files
          </p>
          <div className="flex flex-wrap gap-3">
            {files.pdf && (
              <a
                href={getPdfUrl(results.case_id)}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-2 rounded-lg bg-blue-600 hover:bg-blue-500 px-4 py-2 text-sm font-medium text-white transition"
              >
                <Download size={14} />
                Download PDF Report
              </a>
            )}
            {files.json && (
              <a
                href={getJsonUrl(results.case_id)}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-2 rounded-lg bg-slate-700 hover:bg-slate-600 border border-slate-600 px-4 py-2 text-sm font-medium text-slate-200 transition"
              >
                <Download size={14} />
                Download JSON Export
              </a>
            )}
          </div>
        </div>
      )}

      {/* Reset */}
      <button
        onClick={onReset}
        className="flex items-center justify-center gap-2 rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-700 px-5 py-2.5 text-sm font-medium text-slate-300 transition"
      >
        <RotateCcw size={14} />
        New Analysis
      </button>
    </div>
  )
}
