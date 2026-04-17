import { AlertCircle, CheckCircle2, ChevronRight, Hash, Building2, User, ShoppingCart, Calculator, Lock, Send, RefreshCw as LucideRefresh } from 'lucide-react'
import Pill from './ui/Pill'

export default function ValidationReport({ stages, results, error, onSendToASP, isSubmitting }) {
  const vResult = results.validate?.report
  const aspResult = results.asp
  const ftaResult = results.submit

  if (error && !vResult) {
    return (
      <div className="p-12 text-center text-red-500 bg-red-50 rounded-xl border border-red-100">
        <AlertCircle className="w-12 h-12 mx-auto mb-4 opacity-50" />
        <h3 className="text-lg font-bold">System Error</h3>
        <p className="text-sm opacity-80 mt-1">{error}</p>
      </div>
    )
  }

  if (!vResult) {
    return (
      <div className="p-12 text-center text-[#8899b0] bg-[#f8faff] rounded-xl border border-[#e3eaf7] border-dashed">
        <CheckCircle2 className="w-12 h-12 mx-auto mb-4 opacity-20" />
        <p className="text-sm font-medium">Validation report will appear here</p>
      </div>
    )
  }

  const failedFields = vResult.field_results?.flatMap(g => g.fields.filter(f => f.status === 'fail')) || []

  return (
    <div className="space-y-6">
      {/* 1. Summary Banner */}
      <div className={`p-5 rounded-2xl border-2 flex items-center justify-between transition-all shadow-lg ${
        vResult.is_valid 
          ? 'bg-emerald-50 border-emerald-200' 
          : 'bg-red-50 border-red-200'
      }`}>
        <div className="flex items-center gap-5">
          <div className={`w-14 h-14 rounded-full flex items-center justify-center shadow-inner ${
            vResult.is_valid ? 'bg-emerald-500 text-white' : 'bg-red-500 text-white'
          }`}>
            {vResult.is_valid ? <CheckCircle2 size={28} /> : <AlertCircle size={28} />}
          </div>
          <div>
            <div className="flex items-center gap-3">
              <span className="text-lg font-black text-[#1a2340]">Invoice #{vResult.invoice_number}</span>
              <Pill variant={vResult.is_valid ? 'green' : 'red'} className="px-3 py-1 text-[10px] tracking-widest font-black">
                {vResult.is_valid ? 'COMPLIANT' : 'NON-COMPLIANT'}
              </Pill>
            </div>
            <p className={`text-sm mt-1 font-bold ${vResult.is_valid ? 'text-emerald-700' : 'text-red-700'}`}>
              UAE PINT AE Mandatory Field Coverage: {vResult.metrics.pass_percentage}%
            </p>
          </div>
        </div>
        {!vResult.is_valid && (
          <div className="text-right border-l border-red-200 pl-6">
            <div className="text-3xl font-black text-red-600 leading-none">{vResult.total_errors}</div>
            <div className="text-[10px] font-black text-red-700 uppercase tracking-widest mt-1">Errors Found</div>
          </div>
        )}
      </div>

      {/* 2. Pipeline Guard - Block ASP/FTA if invalid */}
      {!vResult.is_valid && (
        <div className="bg-[#1a2340] text-white p-3 rounded-lg flex items-center gap-3 text-xs font-medium">
          <Lock size={14} className="text-amber-400" />
          <span>Fix {vResult.total_errors} errors before submitting to ASP or FTA clearance.</span>
        </div>
      )}

      {/* 3. Failures First Section (Pinned) */}
      {failedFields.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-[10px] font-bold text-red-500 uppercase tracking-[0.2em] flex items-center gap-2 px-1">
            <AlertCircle size={12} /> Critical Failures
          </h3>
          <div className="grid gap-2">
            {failedFields.map((f, i) => (
              <div key={i} className="bg-white border-l-4 border-l-red-500 border-y border-r border-[#e3eaf7] p-3 rounded-r-lg shadow-sm">
                <div className="flex justify-between items-start mb-1">
                  <span className="text-xs font-bold text-[#1a2340]">{f.label} <span className="text-[#8899b0] font-normal font-mono ml-1">[{f.pint_ref}]</span></span>
                  <span className="text-[10px] bg-red-100 text-red-600 font-black px-1.5 py-0.5 rounded uppercase">Fail</span>
                </div>
                <div className="text-xs text-[#5a6a85] font-mono break-words bg-[#f8faff] p-1.5 rounded border border-[#e3eaf7] mb-2">
                  {f.value}
                </div>
                <div className="text-[11px] text-red-600 flex items-start gap-1.5 leading-relaxed">
                   <ChevronRight size={12} className="mt-0.5 shrink-0" />
                   <span>{f.error}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 4. Grouped Breakdown (The Auditor View) */}
      <div className="space-y-6">
        {vResult.field_results?.map((group, gIdx) => (
          <div key={gIdx} className="space-y-3">
            <h3 className="text-[10px] font-bold text-[#8899b0] uppercase tracking-[0.2em] flex items-center gap-2 px-1">
              {group.group.includes('details') ? <Building2 size={12} /> : 
               group.group.includes('totals') ? <Calculator size={12} /> :
               group.group.includes('items') ? <ShoppingCart size={12} /> : <Hash size={12} />}
              {group.group}
            </h3>
            <div className="bg-white border border-[#e3eaf7] rounded-xl overflow-hidden shadow-sm divide-y divide-[#e3eaf7]">
              {group.fields.map((f, fIdx) => (
                <div key={fIdx} className={`p-3 flex items-start gap-4 group transition-colors ${f.status === 'fail' ? 'bg-red-50/30' : 'hover:bg-[#f8faff]'}`}>
                   <div className="mt-1">
                    {f.status === 'pass' 
                      ? <CheckCircle2 size={14} className="text-emerald-500" /> 
                      : <AlertCircle size={14} className="text-red-500" />
                    }
                   </div>
                   <div className="flex-1 min-w-0">
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-xs font-semibold text-[#1a2340]">
                          {f.label} 
                          <span className="text-[#8899b0] font-normal font-mono text-[10px] ml-1.5">[{f.pint_ref}]</span>
                        </span>
                        <Pill variant={f.status === 'pass' ? 'green' : 'red'}>
                          {f.status.toUpperCase()}
                        </Pill>
                      </div>
                      <div className={`text-xs font-mono truncate py-1 px-1.5 rounded ${f.status === 'fail' ? 'text-red-700 bg-red-100/50' : 'text-[#5a6a85] bg-[#f8faff]'}`}>
                        {f.value}
                      </div>
                      {f.status === 'fail' && (
                        <div className="mt-1.5 text-[11px] text-red-600 bg-white p-2 rounded border border-red-100 shadow-sm leading-relaxed">
                          {f.error}
                        </div>
                      )}
                   </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* 5. Phase 2/3 Results: ASP & FTA */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-[#e3eaf7]">
        
        {/* ASP Card */}
        <div className={`rounded-xl border p-4 shadow-sm transition-all ${
          !vResult.is_valid ? 'opacity-50 grayscale' : 
          aspResult ? 'bg-emerald-50 border-emerald-100' : 'bg-white border-[#e3eaf7]'
        }`}>
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-xs font-bold text-[#1a2340] uppercase tracking-wide">ASP Validation</h3>
            {vResult.is_valid ? (
               aspResult ? <CheckCircle2 size={16} className="text-emerald-500" /> : <RefreshCw size={16} className="text-slate-400 animate-pulse" />
            ) : <Lock size={16} className="text-slate-400" />}
          </div>
          
          <div className="space-y-2">
            {[
              { label: 'Status', val: aspResult?.status || 'IDLE' },
              { label: 'Invoice #', val: vResult.invoice_number || '—' },
              { label: 'Reference', val: aspResult?.asp_reference || '—' },
            ].map(r => (
              <div key={r.label} className="flex justify-between text-[11px] py-1 border-b border-black/5 last:border-0">
                <span className="text-[#8899b0] font-medium">{r.label}</span>
                <span className="text-[#1a2340] font-bold">{r.val}</span>
              </div>
            ))}
          </div>
          {vResult.is_valid && !aspResult && (
            <button 
              onClick={onSendToASP}
              disabled={isSubmitting}
              className="w-full mt-4 py-2 bg-[#1a6fcf] text-white rounded-lg text-[10px] font-black uppercase tracking-widest hover:bg-[#1559a7] transition-all flex items-center justify-center gap-2"
            >
              {isSubmitting ? <LucideRefresh size={12} className="animate-spin" /> : <Send size={12} />}
              Push to ASP Integration
            </button>
          )}
        </div>

        {/* FTA Card */}
        <div className={`rounded-xl border p-4 shadow-sm transition-all ${
          !vResult.is_valid || !aspResult ? 'opacity-50 grayscale' : 
          ftaResult?.status === 'CLEARED' ? 'bg-emerald-500 text-white' : 
          ftaResult?.status === 'REJECTED' ? 'bg-red-500 text-white' : 
          'bg-white border-[#e3eaf7]'
        }`}>
          <div className="flex justify-between items-center mb-4">
            <h3 className={`text-xs font-bold uppercase tracking-wide ${ftaResult ? 'text-white' : 'text-[#1a2340]'}`}>FTA Clearance</h3>
            {ftaResult?.status === 'CLEARED' ? <CheckCircle2 size={16} /> : <Calculator size={16} className={ftaResult ? 'text-white' : 'text-slate-400'} />}
          </div>
          
          <div className="space-y-2">
            {ftaResult ? (
              <>
                <div className="p-2 bg-black/10 rounded font-mono text-center mb-2">
                  <div className="text-[10px] uppercase opacity-60 mb-1">Clearance ID</div>
                  <div className="text-sm font-black break-all">{ftaResult.clearance_id || 'REJECTED'}</div>
                </div>
                {ftaResult.error && <p className="text-[10px] leading-tight italic opacity-90">{ftaResult.error}</p>}
              </>
            ) : (
              <div className="flex justify-between text-[11px]">
                <span className="text-[#8899b0] font-medium">Status</span>
                <span className="text-[#1a2340] font-bold">WAITING</span>
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  )
}

function RefreshCw({ size, className }) {
  return (
    <svg 
      xmlns="http://www.w3.org/2000/svg" 
      width={size} 
      height={size} 
      viewBox="0 0 24 24" 
      fill="none" 
      stroke="currentColor" 
      strokeWidth="2" 
      strokeLinecap="round" 
      strokeLinejoin="round" 
      className={className}
    >
      <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
      <path d="M3 3v5h5" />
      <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16" />
      <path d="M16 16h5v5" />
    </svg>
  )
}
