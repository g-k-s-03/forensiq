import { useState } from 'react'
import { Search, AlertCircle } from 'lucide-react'
import { startAnalysis } from '../api/client'

const Toggle = ({ checked, onChange, label }) => (
  <label className="flex items-center gap-3 cursor-pointer select-none">
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-slate-800 ${
        checked ? 'bg-blue-500' : 'bg-slate-600'
      }`}
    >
      <span
        className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
          checked ? 'translate-x-6' : 'translate-x-1'
        }`}
      />
    </button>
    <span className="text-sm text-slate-300">{label}</span>
  </label>
)

const Field = ({ label, required, children }) => (
  <div className="flex flex-col gap-1.5">
    <label className="text-sm font-medium text-slate-300">
      {label}{required && <span className="text-red-400 ml-1">*</span>}
    </label>
    {children}
  </div>
)

const inputCls =
  'w-full rounded-lg bg-slate-900 border border-slate-700 text-slate-100 placeholder-slate-500 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition'

export default function CaseForm({ onJobStarted }) {
  const [form, setForm] = useState({
    evidence_dir: '',
    case_id: '',
    investigator: '',
    device_info: '',
    baseline_path: '',
    generate_pdf: true,
    export_json: false,
  })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      const payload = {
        evidence_dir: form.evidence_dir,
        case_id: form.case_id,
        investigator: form.investigator,
        device_info: form.device_info || 'Unknown Device',
        generate_pdf: form.generate_pdf,
        export_json: form.export_json,
      }
      if (form.baseline_path) payload.baseline_path = form.baseline_path
      const { job_id } = await startAnalysis(payload)
      onJobStarted(job_id, form.case_id)
    } catch (err) {
      const msg =
        err.response?.data?.detail || err.message || 'Failed to start analysis.'
      setError(msg)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-5">
      <Field label="Evidence Directory" required>
        <input
          className={inputCls}
          placeholder="./sample_evidence"
          value={form.evidence_dir}
          onChange={set('evidence_dir')}
          disabled={submitting}
          required
        />
      </Field>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
        <Field label="Case ID" required>
          <input
            className={inputCls}
            placeholder="CASE-001"
            value={form.case_id}
            onChange={set('case_id')}
            disabled={submitting}
            required
          />
        </Field>
        <Field label="Investigator Name" required>
          <input
            className={inputCls}
            placeholder="Full name"
            value={form.investigator}
            onChange={set('investigator')}
            disabled={submitting}
            required
          />
        </Field>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
        <Field label="Device Info">
          <input
            className={inputCls}
            placeholder="Unknown Device"
            value={form.device_info}
            onChange={set('device_info')}
            disabled={submitting}
          />
        </Field>
        <Field label="Baseline Path">
          <input
            className={inputCls}
            placeholder="baseline.json"
            value={form.baseline_path}
            onChange={set('baseline_path')}
            disabled={submitting}
          />
        </Field>
      </div>

      <div className="flex flex-col sm:flex-row gap-5 pt-1">
        <Toggle
          checked={form.generate_pdf}
          onChange={(v) => setForm((f) => ({ ...f, generate_pdf: v }))}
          label="Generate PDF Report"
        />
        <Toggle
          checked={form.export_json}
          onChange={(v) => setForm((f) => ({ ...f, export_json: v }))}
          label="Export Full JSON"
        />
      </div>

      {error && (
        <div className="flex items-start gap-2 rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          <AlertCircle size={16} className="mt-0.5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <button
        type="submit"
        disabled={submitting}
        className="mt-1 flex items-center justify-center gap-2 rounded-lg bg-blue-600 px-6 py-3 text-sm font-semibold text-white transition hover:bg-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-slate-800 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <Search size={16} />
        {submitting ? 'Starting…' : 'Start Analysis'}
      </button>
    </form>
  )
}
