import { RotateCcw } from 'lucide-react'
import DownloadBar from './DownloadBar'
import ResultsTabs from './ResultsTabs'

export default function ResultsView({ results, caseId, onNewAnalysis }) {
  const outputFiles = results.output_files ?? {}

  return (
    <div className="w-full max-w-7xl mx-auto px-4 py-6 flex flex-col gap-4">
      {/* Top bar */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-col gap-0.5">
          <h2 className="font-mono text-2xl font-bold text-slate-100 tracking-tight">
            {caseId}
          </h2>
          <p className="text-xs text-slate-500">
            Analysis complete · {results.analysis_time}
          </p>
        </div>
        <button
          onClick={onNewAnalysis}
          className="flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-700 px-4 py-2 text-sm font-medium text-slate-300 transition"
        >
          <RotateCcw size={14} />
          New Analysis
        </button>
      </div>

      {/* Download bar */}
      <DownloadBar
        caseId={caseId}
        analysisTime={results.analysis_time}
        outputFiles={outputFiles}
      />

      {/* Tabs: overview, tamper flags, browser, timeline */}
      <div className="rounded-xl border border-slate-700/50 bg-slate-800/30 px-5 py-4">
        <ResultsTabs results={results} />
      </div>
    </div>
  )
}
