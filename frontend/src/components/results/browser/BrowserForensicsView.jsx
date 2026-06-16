import { Globe, Download, Cookie, Wifi } from 'lucide-react'
import BrowserTabs from './BrowserTabs'

function Stat({ icon: Icon, label, value, sub }) {
  return (
    <div className="flex items-center gap-2 text-xs text-slate-400">
      <Icon size={13} className="text-slate-500" />
      <span className="font-mono font-semibold text-slate-200">{value}</span>
      <span>{label}</span>
      {sub && <span className="text-slate-600">({sub})</span>}
    </div>
  )
}

export default function BrowserForensicsView({
  browserHistory = [],
  downloads = [],
  cookies = [],
  dnsCcache = [],
}) {
  const recovered = browserHistory.filter((r) => r.recovered).length
  const live      = browserHistory.length - recovered

  return (
    <div className="flex flex-col gap-5">
      {/* Summary row */}
      <div className="flex flex-wrap gap-x-6 gap-y-2 px-1 py-2 border-b border-slate-700/50">
        <Stat
          icon={Globe}
          label="history records"
          value={browserHistory.length}
          sub={`${recovered} recovered`}
        />
        <Stat
          icon={Download}
          label="downloads"
          value={downloads.length}
        />
        <Stat
          icon={Cookie}
          label="cookies"
          value={cookies.length}
        />
        <Stat
          icon={Wifi}
          label="DNS entries"
          value={dnsCcache.length}
        />
      </div>

      {/* Sub-tabs */}
      <BrowserTabs
        browserHistory={browserHistory}
        downloads={downloads}
        cookies={cookies}
        dnsCcache={dnsCcache}
      />
    </div>
  )
}
