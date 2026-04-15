import { useState, useMemo } from 'react'
import { Copy, Check, RotateCcw, AlertCircle } from 'lucide-react'
import { SAMPLES, DEMO_API_KEY } from '../constants/samplePayloads'

export default function PayloadEditor({ value, onChange, apiKey, onApiKeyChange, validationErrors = [], totalErrors = 0 }) {
  const [copied, setCopied] = useState(false)
  const [jsonError, setJsonError] = useState(null)

  const handleChange = (val) => {
    onChange(val)
    try { JSON.parse(val); setJsonError(null) }
    catch (e) { setJsonError(e.message) }
  }

  const loadSample = (key) => {
    const json = JSON.stringify(SAMPLES[key].payload, null, 2)
    handleChange(json)
  }

  const copyPayload = async () => {
    await navigator.clipboard.writeText(value)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  const formatJson = () => {
    try {
      const formatted = JSON.stringify(JSON.parse(value), null, 2)
      handleChange(formatted)
    } catch {}
  }

  // Error highlighting logic
  const errorLines = useMemo(() => {
    if (!validationErrors.length) return []
    const lines = value.split('\n')
    return validationErrors.map(err => {
      const fieldKey = err.field
      // Look for exactly "key": (handling potential whitespace)
      const keyPattern = new RegExp(`"${fieldKey}"\\s*:`)
      const index = lines.findIndex(l => keyPattern.test(l))
      
      return { 
        line: index >= 0 ? index + 1 : null, 
        field: fieldKey, 
        msg: err.error 
      }
    }).filter(e => e.line !== null)
  }, [validationErrors, value])

  return (
    <div className="flex flex-col h-full gap-3">

      {/* Sample loaders */}
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-xs text-[#5a6a85] mb-2 font-medium uppercase tracking-wider">Load sample</p>
          <div className="flex flex-wrap gap-2">
            {Object.entries(SAMPLES).map(([key, { label, color }]) => (
              <button
                key={key}
                onClick={() => loadSample(key)}
                className={`px-3 py-1.5 text-xs font-medium rounded-md border border-[#e3eaf7] hover:border-slate-500 bg-white hover:bg-[#f8faff] transition-all ${color}`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
        
        {totalErrors > 0 && (
           <div className="bg-red-50 border border-red-200 rounded-lg px-3 py-2 flex items-center gap-2 text-red-600 animate-pulse">
             <AlertCircle size={14} />
             <div className="flex flex-col">
               <span className="text-xs font-bold font-mono">{totalErrors} FIELD ERRORS</span>
               {totalErrors > errorLines.length && (
                 <span className="text-[9px] font-medium opacity-80 decoration-dotted underline cursor-help" title="Some errors (like mathematical sums or missing mandatory fields) cannot be highlighted on a specific line.">
                   +{totalErrors - errorLines.length} implicit/missing
                 </span>
               )}
             </div>
           </div>
        )}
      </div>

      {/* API key */}
      <div className="flex items-center gap-2">
        <label className="text-xs text-[#5a6a85] whitespace-nowrap font-medium">API key</label>
        <input
          type="text"
          value={apiKey}
          onChange={e => onApiKeyChange(e.target.value)}
          placeholder="demo-key-123"
          className="flex-1 px-3 py-1.5 text-xs bg-white border border-[#e3eaf7] rounded-md text-[#1a2340] placeholder-slate-600 focus:outline-none focus:border-sky-500 font-mono"
        />
      </div>

      {/* Editor header */}
      <div className="flex items-center justify-between">
        <span className="text-xs text-[#5a6a85] font-medium uppercase tracking-wider">Payload JSON</span>
        <div className="flex items-center gap-1">
          {jsonError && (
            <span className="text-xs text-red-400 mr-2 max-w-48 truncate" title={jsonError}>
              ✗ {jsonError}
            </span>
          )}
          <button onClick={formatJson} className="p-1.5 text-[#5a6a85] hover:text-[#1a2340] hover:bg-[#f8faff] rounded transition-colors" title="Format JSON">
            <RotateCcw size={13} />
          </button>
          <button onClick={copyPayload} className="p-1.5 text-[#5a6a85] hover:text-[#1a2340] hover:bg-[#f8faff] rounded transition-colors" title="Copy">
            {copied ? <Check size={13} className="text-emerald-400" /> : <Copy size={13} />}
          </button>
        </div>
      </div>

      {/* Textarea with relative overlay */}
      <div className="flex-1 relative group flex flex-col">
        {/* Error overlay (Backdrop) */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden font-mono text-[13px] leading-[22px] p-4 whitespace-pre">
          {value.split('\n').map((_, i) => {
            const err = errorLines.find(e => e.line === i + 1);
            return (
              <div 
                key={i} 
                className={`w-full h-[22px] flex items-center ${err ? 'bg-red-500/10 border-l-2 border-red-500' : ''}`}
              >
                {err && (
                  <div className="ml-auto flex items-center pr-2 max-w-[40%] overflow-hidden">
                     <span className="text-[9px] font-bold text-red-500 px-1 bg-white border border-red-200 rounded uppercase tracking-tighter mr-6 truncate">
                       {err.field} Fail
                     </span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
        
        <textarea
          className="json-editor flex-1 w-full font-mono text-[13px] leading-[22px] bg-transparent relative z-10 resize-none p-4 whitespace-pre overflow-x-auto"
          style={{ minHeight: 0, color: 'inherit', whiteSpace: 'pre', overflowWrap: 'normal' }}
          value={value}
          onChange={e => handleChange(e.target.value)}
          spellCheck={false}
          autoComplete="off"
          wrap="off"
        />
        
        {jsonError && (
          <div className="absolute bottom-3 left-3 right-3 h-0.5 bg-red-500/40 rounded" />
        )}
      </div>

    </div>
  )
}
