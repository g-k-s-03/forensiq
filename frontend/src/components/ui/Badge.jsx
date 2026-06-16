const COLOR = {
  red:    'bg-red-900/70 text-red-300 border border-red-700/40',
  green:  'bg-green-900/70 text-green-300 border border-green-700/40',
  blue:   'bg-blue-900/70 text-blue-300 border border-blue-700/40',
  yellow: 'bg-yellow-900/70 text-yellow-300 border border-yellow-700/40',
  cyan:   'bg-cyan-900/70 text-cyan-300 border border-cyan-700/40',
  slate:  'bg-slate-700/70 text-slate-300 border border-slate-600/40',
  orange: 'bg-orange-900/70 text-orange-300 border border-orange-700/40',
}

export default function Badge({ color = 'slate', children, className = '' }) {
  return (
    <span
      className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium ${COLOR[color] ?? COLOR.slate} ${className}`}
    >
      {children}
    </span>
  )
}
