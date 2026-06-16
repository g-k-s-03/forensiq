import { useState } from 'react'
import HistoryTable from './HistoryTable'
import DownloadsTable from './DownloadsTable'
import CookiesTable from './CookiesTable'
import DnsCacheTable from './DnsCacheTable'

function SubTab({ label, active, count, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-3 py-2 text-xs font-medium border-b-2 transition-colors whitespace-nowrap ${
        active
          ? 'border-blue-500 text-white'
          : 'border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-600'
      }`}
    >
      {label}
      {count != null && count > 0 && (
        <span className="inline-flex items-center justify-center min-w-[1.25rem] h-4 px-1 rounded-full text-xs font-bold bg-slate-700 text-slate-300">
          {count}
        </span>
      )}
    </button>
  )
}

export default function BrowserTabs({ browserHistory = [], downloads = [], cookies = [], dnsCcache = [] }) {
  const [active, setActive] = useState('history')

  return (
    <div className="flex flex-col gap-4">
      {/* Sub-tab bar */}
      <div className="flex border-b border-slate-700/60 overflow-x-auto">
        <SubTab
          label="History"
          active={active === 'history'}
          count={browserHistory.length}
          onClick={() => setActive('history')}
        />
        <SubTab
          label="Downloads"
          active={active === 'downloads'}
          count={downloads.length}
          onClick={() => setActive('downloads')}
        />
        <SubTab
          label="Cookies"
          active={active === 'cookies'}
          count={cookies.length}
          onClick={() => setActive('cookies')}
        />
        <SubTab
          label="DNS Cache"
          active={active === 'dns'}
          count={dnsCcache.length}
          onClick={() => setActive('dns')}
        />
      </div>

      {/* Content */}
      {active === 'history'   && <HistoryTable   history={browserHistory} />}
      {active === 'downloads' && <DownloadsTable downloads={downloads} />}
      {active === 'cookies'   && <CookiesTable   cookies={cookies} />}
      {active === 'dns'       && <DnsCacheTable  dnsCcache={dnsCcache} />}
    </div>
  )
}
