import { CheckCircle2, XCircle, Clock } from 'lucide-react'

export default function SessionHistory({ history, onReload }) {
  if (!history.length) return (
    <p className="text-xs text-slate-600 text-center py-4">No runs this session</p>
  )

  return (
    <div className="flex flex-col gap-1.5">
      {history.slice().reverse().map((run, i) => (
        <button
          key={i}
          onClick={() => onReload(run.payload)}
          className="flex items-center gap-3 px-3 py-2 rounded-lg bg-white hover:bg-[#f8faff] border border-[#e3eaf7] hover:border-[#e3eaf7] transition-all text-left group"
        >
          {run.valid
            ? <CheckCircle2 size={13} className="text-emerald-400 flex-shrink-0" />
            : <XCircle size={13} className="text-red-400 flex-shrink-0" />
          }
          <div className="flex-1 min-w-0">
            <p className="text-xs font-mono text-[#1a2340] truncate">{run.invoiceNumber || 'unknown'}</p>
            <p className="text-xs text-slate-600">{run.type} · {run.errorCount} error{run.errorCount !== 1 ? 's' : ''}</p>
          </div>
          <span className="text-xs text-slate-700 group-hover:text-[#5a6a85] flex items-center gap-1">
            <Clock size={10} /> {run.time}
          </span>
        </button>
      ))}
    </div>
  )
}
