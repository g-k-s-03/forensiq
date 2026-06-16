export default function Table({
  columns,
  rows,
  emptyMessage = 'No data found.',
  rowClass,
  maxHeight = 'max-h-96',
}) {
  return (
    <div className="rounded-lg border border-slate-700 overflow-hidden">
      <div className={`${maxHeight} overflow-y-auto`}>
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-700 sticky top-0 z-10">
              {columns.map((col) => (
                <th
                  key={col.key}
                  className="px-3 py-2.5 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider whitespace-nowrap"
                  style={col.width ? { width: col.width } : {}}
                >
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/80">
            {rows.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-4 py-8 text-center text-slate-500 text-xs"
                >
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              rows.map((row, i) => (
                <tr
                  key={i}
                  className={`transition-colors hover:bg-slate-700/40 ${
                    rowClass
                      ? rowClass(row, i)
                      : i % 2 === 0
                      ? 'bg-slate-800/40'
                      : 'bg-slate-800/70'
                  }`}
                >
                  {columns.map((col) => (
                    <td key={col.key} className="px-3 py-2.5 text-xs">
                      {col.render
                        ? col.render(row[col.key], row)
                        : row[col.key] != null
                        ? String(row[col.key])
                        : '—'}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
