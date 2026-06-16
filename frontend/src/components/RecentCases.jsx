import { useEffect, useState } from 'react'
import { FolderOpen, RefreshCw, FileText, Download as DlIcon } from 'lucide-react'
import { listReports, getPdfUrl, getJsonUrl } from '../api/client'

export default function RecentCases() {
  const [cases, setCases]   = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError]   = useState(null)

  const load = () => {
    setLoading(true)
    setError(null)
    listReports()
      .then((data) => setCases(data.cases ?? []))
      .catch(() => setError('Could not load recent cases.'))
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  if (loading) {
    return (
      <div className="mt-4 text-center text-slate-500 text-xs py-4">
        Loading recent cases…
      </div>
    )
  }

  if (error) {
    return (
      <div className="mt-4 flex items-center justify-between bg-slate-800/60 border border-slate-700 rounded-lg px-4 py-3">
        <span className="text-red-400 text-xs">{error}</span>
        <button onClick={load} className="text-slate-400 hover:text-white transition-colors">
          <RefreshCw size={13} />
        </button>
      </div>
    )
  }

  if (cases.length === 0) {
    return (
      <div className="mt-4 text-center text-slate-600 text-xs py-4">
        No previous cases found.
      </div>
    )
  }

  return (
    <div className="mt-6">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-slate-400 text-xs font-semibold uppercase tracking-wider flex items-center gap-1.5">
          <FolderOpen size={12} /> Recent Cases
        </h3>
        <button
          onClick={load}
          title="Refresh"
          className="text-slate-500 hover:text-slate-300 transition-colors"
        >
          <RefreshCw size={12} />
        </button>
      </div>

      <div className="flex flex-col gap-2">
        {cases.map((c) => (
          <div
            key={c.case_id}
            className="flex items-center justify-between bg-slate-800/60 border border-slate-700/60 rounded-lg px-4 py-3 hover:border-slate-600 transition-colors"
          >
            <div className="flex items-center gap-2 min-w-0">
              <FileText size={13} className="text-slate-500 flex-shrink-0" />
              <span className="text-sm text-slate-300 font-mono truncate">{c.case_id}</span>
            </div>
            <div className="flex items-center gap-2 ml-3 flex-shrink-0">
              {c.has_pdf && (
                <a
                  href={getPdfUrl(c.case_id)}
                  target="_blank"
                  rel="noreferrer"
                  title="Download PDF"
                  className="text-blue-400 hover:text-blue-300 transition-colors"
                >
                  <DlIcon size={13} />
                </a>
              )}
              {c.has_json && (
                <a
                  href={getJsonUrl(c.case_id)}
                  target="_blank"
                  rel="noreferrer"
                  title="Download JSON"
                  className="text-slate-400 hover:text-slate-200 text-xs transition-colors"
                >
                  JSON
                </a>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
