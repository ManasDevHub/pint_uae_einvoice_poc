import { Play, ChevronRight, Loader2 } from 'lucide-react'

const STAGES = [
  { key: 'validate', label: 'Validate',  sub: '/api/v1/validate-invoice', endpoint: '/api/v1/validate-invoice' },
  { key: 'asp',      label: 'ASP mock',  sub: '/asp/v1/validate',         endpoint: '/asp/v1/validate' },
  { key: 'submit',   label: 'FTA submit',sub: '/asp/v1/submit',           endpoint: '/asp/v1/submit' },
]

const stageIcon = {
  idle:    <span className="w-5 h-5 rounded-full border border-current flex items-center justify-center text-xs">–</span>,
  loading: <Loader2 size={16} className="animate-spin" />,
  success: <span className="w-5 h-5 rounded-full border border-current flex items-center justify-center text-xs">✓</span>,
  error:   <span className="w-5 h-5 rounded-full border border-current flex items-center justify-center text-xs">✗</span>,
  blocked: <span className="w-5 h-5 rounded-full border border-current flex items-center justify-center text-xs opacity-40 group-hover:opacity-100">–</span>,
}

export default function PipelineRunner({ stages, isRunning, onRunAll, onRunSingle, onReset }) {
  return (
    <div className="flex flex-col gap-4">

      {/* Pipeline stages visual */}
      <div className="flex items-center gap-1">
        {STAGES.map((s, i) => (
          <div key={s.key} className="flex items-center gap-1 flex-1">
            <button
               onClick={() => onRunSingle(s.endpoint)}
              disabled={isRunning}
              className={`stage-${stages[s.key]} flex-1 flex items-center gap-2 px-3 py-2.5 rounded-lg border text-xs font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:brightness-110`}
              title={`Run ${s.label} only`}
            >
              {stageIcon[stages[s.key]]}
              <div className="text-left">
                <div>{s.label}</div>
                <div className="opacity-50 font-normal" style={{ fontSize: 10 }}>{s.sub}</div>
              </div>
            </button>
            {i < STAGES.length - 1 && (
              <ChevronRight size={14} className="text-slate-700 flex-shrink-0" />
            )}
          </div>
        ))}
      </div>

      {/* Primary action */}
      <div className="flex gap-2">
        <button
          onClick={onRunAll}
          disabled={isRunning}
          className="flex-1 flex items-center justify-center gap-2 py-2.5 px-4 bg-sky-600 hover:bg-sky-500 disabled:bg-slate-700 disabled:cursor-not-allowed text-[#1a2340] text-sm font-semibold rounded-lg transition-all"
        >
          {isRunning
            ? <><Loader2 size={15} className="animate-spin" /> Running pipeline...</>
            : <><Play size={15} /> Run full pipeline</>
          }
        </button>
        <button
          onClick={onReset}
          disabled={isRunning}
         className="px-4 py-2.5 text-sm text-[#8899b0] hover:text-slate-200 border border-[#e3eaf7] hover:border-slate-500 rounded-lg transition-all disabled:opacity-50"
        >
          Reset
        </button>
      </div>

    </div>
  )
}
