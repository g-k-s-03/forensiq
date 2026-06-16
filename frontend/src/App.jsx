import { useState } from 'react'
import Header from './components/Header'
import CaseForm from './components/CaseForm'
import ProgressStream from './components/ProgressStream'
import ResultsView from './components/results/ResultsView'
import RecentCases from './components/RecentCases'

const NarrowCard = ({ title, subtitle, children }) => (
  <div className="w-full max-w-2xl rounded-2xl border border-slate-700/60 bg-slate-800 shadow-2xl shadow-black/40 p-7">
    {(title || subtitle) && (
      <div className="mb-6">
        {title && <h2 className="text-lg font-semibold text-slate-100">{title}</h2>}
        {subtitle && <p className="text-sm text-slate-400 mt-1">{subtitle}</p>}
      </div>
    )}
    {children}
  </div>
)

export default function App() {
  const [view, setView]       = useState('new')
  const [jobId, setJobId]     = useState(null)
  const [caseId, setCaseId]   = useState(null)
  const [results, setResults] = useState(null)

  const handleJobStarted = (id, cid) => {
    setJobId(id)
    setCaseId(cid)
    setView('analyzing')
  }

  const handleComplete = (res) => {
    setResults(res)
    setView('results')
  }

  const handleReset = () => {
    setView('new')
    setJobId(null)
    setCaseId(null)
    setResults(null)
  }

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100">
      <Header />

      {/* Centered layout for new / analyzing views */}
      {(view === 'new' || view === 'analyzing') && (
        <main className="flex flex-col items-center justify-start px-4 pt-24 pb-16">
          {view === 'new' && (
            <>
              <div className="mb-8 text-center">
                <h1 className="text-4xl font-bold tracking-tight text-slate-100">
                  Foren<span className="text-blue-400">IQ</span>
                </h1>
                <p className="mt-2 text-slate-400 text-sm">
                  Digital Forensics Evidence Analyzer
                </p>
              </div>
              <NarrowCard
                title="New Analysis"
                subtitle="Provide the evidence directory path and case details to begin."
              >
                <CaseForm onJobStarted={handleJobStarted} />
              </NarrowCard>
              <div className="w-full max-w-2xl mt-2">
                <RecentCases />
              </div>
            </>
          )}

          {view === 'analyzing' && (
            <NarrowCard
              title="Running Analysis"
              subtitle="The forensics pipeline is processing your evidence."
            >
              <ProgressStream
                jobId={jobId}
                caseId={caseId}
                onComplete={handleComplete}
              />
            </NarrowCard>
          )}
        </main>
      )}

      {/* Full-width results view */}
      {view === 'results' && results && (
        <main className="pt-16">
          <ResultsView
            results={results}
            caseId={caseId}
            onNewAnalysis={handleReset}
          />
        </main>
      )}
    </div>
  )
}
