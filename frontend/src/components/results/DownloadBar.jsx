import { FileText, Download, Hash, Clock } from 'lucide-react'
import {
  getPdfUrl,
  getJsonUrl,
  getHashesUrl,
  getTimelineUrl,
} from '../../api/client'

function DlBtn({ href, icon: Icon, label, primary }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className={`flex items-center gap-2 rounded-full px-4 py-2 text-xs font-medium transition ${
        primary
          ? 'bg-blue-600 hover:bg-blue-500 text-white'
          : 'bg-slate-700 hover:bg-slate-600 border border-slate-600 text-slate-200'
      }`}
    >
      <Icon size={13} />
      {label}
    </a>
  )
}

export default function DownloadBar({ caseId, analysisTime, outputFiles = {} }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-slate-700/50 bg-slate-800/40 px-5 py-3">
      <div className="flex flex-col">
        <span className="font-mono text-sm font-semibold text-slate-200">{caseId}</span>
        <span className="text-xs text-slate-500 mt-0.5">{analysisTime}</span>
      </div>

      <div className="flex flex-wrap gap-2">
        {outputFiles.pdf && (
          <DlBtn
            href={getPdfUrl(caseId)}
            icon={FileText}
            label="PDF Report"
            primary
          />
        )}
        {outputFiles.json && (
          <DlBtn
            href={getJsonUrl(caseId)}
            icon={Download}
            label="JSON Export"
          />
        )}
        <DlBtn
          href={getHashesUrl(caseId)}
          icon={Hash}
          label="Hash Manifest"
        />
        <DlBtn
          href={getTimelineUrl(caseId)}
          icon={Clock}
          label="Timeline JSON"
        />
      </div>
    </div>
  )
}
