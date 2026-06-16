import { useEffect, useRef, useState } from 'react'
import { CheckCircle, Circle, AlertCircle, Loader, Timer } from 'lucide-react'
import { getJobResults } from '../api/client'

const fmtElapsed = (s) =>
  s < 60 ? `${s}s` : `${Math.floor(s / 60)}m ${s % 60}s`

const STEPS = [
  { label: 'Metadata Extraction',   threshold: 10 },
  { label: 'Hash & Tamper Detection', threshold: 30 },
  { label: 'Browser Forensics',     threshold: 50 },
  { label: 'Timeline Builder',      threshold: 70 },
  { label: 'PDF Report',            threshold: 85 },
  { label: 'Finalizing',            threshold: 95 },
]

export default function ProgressStream({ jobId, caseId, onComplete }) {
  const [progress, setProgress]   = useState(0)
  const [step, setStep]           = useState('Connecting…')
  const [status, setStatus]       = useState('running')
  const [error, setError]         = useState(null)
  const [elapsed, setElapsed]     = useState(0)
  const esRef     = useRef(null)
  const timerRef  = useRef(null)

  useEffect(() => {
    timerRef.current = setInterval(() => setElapsed((s) => s + 1), 1000)
    return () => clearInterval(timerRef.current)
  }, [])

  useEffect(() => {
    if (status === 'complete' || status === 'failed') {
      clearInterval(timerRef.current)
    }
  }, [status])

  useEffect(() => {
    const es = new EventSource(
      `http://localhost:8000/api/analyze/${jobId}/stream`
    )
    esRef.current = es

    es.onmessage = async (e) => {
      try {
        const data = JSON.parse(e.data)
        setProgress(data.progress ?? 0)
        setStep(data.step ?? data.status ?? '')
        setStatus(data.status)

        if (data.status === 'complete') {
          es.close()
          try {
            const results = await getJobResults(jobId)
            onComplete(results)
          } catch (err) {
            setError('Analysis complete but failed to fetch results: ' + err.message)
          }
        } else if (data.status === 'failed') {
          es.close()
          setError(data.error ?? 'Pipeline failed.')
        }
      } catch {
        // ignore parse errors
      }
    }

    es.onerror = () => {
      if (es.readyState === EventSource.CLOSED) return
      es.close()
      setError('Lost connection to server.')
      setStatus('failed')
    }

    return () => es.close()
  }, [jobId]) // eslint-disable-line react-hooks/exhaustive-deps

  const running = status === 'running' || status === 'pending'

  return (
    <div className="flex flex-col gap-6">
      {/* Case info */}
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-slate-400">
        <span>
          Case: <span className="font-mono text-slate-200">{caseId}</span>
        </span>
        <span className="text-slate-600">|</span>
        <span>
          Job: <span className="font-mono text-slate-400 text-xs">{jobId}</span>
        </span>
      </div>

      {/* Progress bar */}
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between text-sm">
          <span className="text-slate-400">{step}</span>
          <div className="flex items-center gap-3">
              <span className="flex items-center gap-1 text-xs text-slate-500 font-mono">
                <Timer size={11} />
                {fmtElapsed(elapsed)}
              </span>
              <span className="font-mono font-semibold text-blue-400">{progress}%</span>
            </div>
        </div>
        <div className="h-3 w-full overflow-hidden rounded-full bg-slate-700">
          <div
            className={`h-full rounded-full bg-blue-500 transition-all duration-500 ${
              running ? 'animate-pulse' : ''
            }`}
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Step indicators */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {STEPS.map(({ label, threshold }) => {
          const done = progress >= threshold
          const active = !done && progress >= threshold - 20 && running
          return (
            <div
              key={label}
              className={`flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition-colors ${
                done
                  ? 'bg-green-500/10 text-green-400'
                  : active
                  ? 'bg-blue-500/10 text-blue-300'
                  : 'text-slate-500'
              }`}
            >
              {done ? (
                <CheckCircle size={15} className="shrink-0 text-green-400" />
              ) : active ? (
                <Loader size={15} className="shrink-0 animate-spin text-blue-400" />
              ) : (
                <Circle size={15} className="shrink-0" />
              )}
              {label}
            </div>
          )
        })}
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-start gap-2 rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          <AlertCircle size={16} className="mt-0.5 shrink-0" />
          <span>{error}</span>
        </div>
      )}
    </div>
  )
}
