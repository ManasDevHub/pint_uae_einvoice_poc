import { useState, useCallback, useEffect } from 'react'
import PayloadEditor from '../components/PayloadEditor'
import PipelineRunner from '../components/PipelineRunner'
import ValidationReport from '../components/ValidationReport'
import SessionHistory from '../components/SessionHistory'
import { useInvoiceApi } from '../hooks/useInvoiceApi'
import { SAMPLES, DEMO_API_KEY } from '../constants/samplePayloads'
import toast from 'react-hot-toast'
import { API_BASE } from '../constants/api'
import { API_HEADERS } from '../constants/apiHelpers'

const DEFAULT_PAYLOAD = JSON.stringify(SAMPLES.b2b.payload, null, 2)

export default function Validate() {
  const [payload, setPayload] = useState(DEFAULT_PAYLOAD)
  const [apiKey, setApiKey] = useState(DEMO_API_KEY)
  const [history, setHistory] = useState([])
  const [lastAddedTimestamp, setLastAddedTimestamp] = useState(null)

  const [fullPipeline, setFullPipeline] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { stages, results, error, isRunning, runPipeline, runSingle, reset, setResults } = useInvoiceApi()

  const addToHistory = useCallback((payloadStr, validateResult) => {
    if (!validateResult?.report) return
    const r = validateResult.report
    setHistory(h => [...h, {
      invoiceNumber: r.invoice_number,
      valid: r.is_valid,
      errorCount: r.total_errors ?? r.errors?.length ?? 0,
      type: (() => { try { return JSON.parse(payloadStr)?.transaction_type || 'unknown' } catch { return 'unknown' } })(),
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      payload: payloadStr,
    }])
  }, [])

  const handleRunSingle = async (endpoint) => {
    await runSingle(endpoint, payload, apiKey, fullPipeline)
  }

  const wrappedRunAll = async () => {
    reset()
    await runPipeline(payload, apiKey, fullPipeline)
  }

  const handleSendToASP = async () => {
    let parsed
    try { parsed = JSON.parse(payload) } catch { return toast.error("Invalid JSON payload") }

    setIsSubmitting(true)
    const t = toast.loading("Pushing to ASP Integration Portal...")
    try {
      // Use the invoice number from the validation results if available, otherwise from parsed payload
      const invNum = results.validate?.report?.invoice_number || parsed.invoice_number || "Unknown"
      
      const res = await fetch(`${API_BASE}/asp/v1/submit?client_id=demo-client-phase2&source_module=Manual%20Workspace&source_filename=manual_entry.json`, {
        method: 'POST',
        headers: API_HEADERS,
        body: JSON.stringify(parsed)
      })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      toast.success(`Invoice #${invNum} cleared by ASP and logged in Audit Portal`, { id: t })
      
      // Update results UI to show the ASP/FTA status
      setResults(prev => ({
        ...prev,
        asp: { status: "ACCEPTED", asp_reference: data.fta_reference }, 
        submit: { status: "CLEARED", clearance_id: data.clearance_id }
      }))
    } catch (e) {
      toast.error("ASP Submission failed: " + e.message, { id: t })
    } finally {
      setIsSubmitting(false)
    }
  }

  useEffect(() => {
    const report = results.validate?.report
    if (report && report.timestamp !== lastAddedTimestamp) {
      addToHistory(payload, results.validate)
      setLastAddedTimestamp(report.timestamp)
    }
  }, [results.validate, addToHistory, payload, lastAddedTimestamp])

  return (
    <div className="space-y-6 max-w-[1600px]">
      <div>
        <h1 className="text-2xl font-bold text-[#1a2340]">Validation Workspace</h1>
        <p className="text-sm text-[#5a6a85] mt-1">UAE PINT AE · 51 mandatory field coverage · ERP adapter layer</p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_320px] gap-6 items-start">
        
        {/* Left: Editor */}
        <div className="bg-white border border-[#e3eaf7] rounded-xl p-5 shadow-sm min-h-[600px] flex flex-col h-full overflow-hidden">
          <h2 className="text-sm font-semibold text-[#8899b0] uppercase tracking-wider mb-4">Invoice payload</h2>
          <div className="flex-1 w-full bg-[#f8faff] rounded-lg overflow-hidden border border-[#e3eaf7] flex flex-col">
             <PayloadEditor
              value={payload}
              onChange={setPayload}
              apiKey={apiKey}
              onApiKeyChange={setApiKey}
              validationErrors={results.validate?.report?.errors || []}
              totalErrors={results.validate?.report?.total_errors || 0}
            />
          </div>
        </div>

        {/* Middle: Pipeline + Results */}
        <div className="flex flex-col gap-6">
          <div className="bg-white border border-[#e3eaf7] rounded-xl p-5 shadow-sm">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-sm font-semibold text-[#8899b0] uppercase tracking-wider">Pipeline</h2>
              <label className="flex items-center gap-2 cursor-pointer group">
                <span className="text-xs font-semibold text-[#5a6a85] group-hover:text-[#1a6fcf] transition-colors">Full Pipeline (Peppol API)</span>
                <div className="relative inline-block w-8 h-4">
                  <input 
                    type="checkbox" 
                    className="peer opacity-0 w-0 h-0" 
                    checked={fullPipeline}
                    onChange={(e) => setFullPipeline(e.target.checked)}
                  />
                  <span className="absolute cursor-pointer inset-0 bg-[#e3eaf7] peer-checked:bg-[#22c55e] rounded-full transition-all before:content-[''] before:absolute before:h-3 before:w-3 before:left-0.5 before:bottom-0.5 before:bg-white before:rounded-full before:transition-all peer-checked:before:translate-x-4"></span>
                </div>
              </label>
            </div>
            <PipelineRunner
              stages={stages}
              isRunning={isRunning}
              onRunAll={wrappedRunAll}
              onRunSingle={handleRunSingle}
              onReset={reset}
            />
          </div>

          <div className="bg-white border border-[#e3eaf7] rounded-xl p-5 shadow-sm flex-1">
            <h2 className="text-sm font-semibold text-[#8899b0] uppercase tracking-wider mb-4">Results</h2>
            <ValidationReport 
              stages={stages} 
              results={results} 
              error={error} 
              onSendToASP={handleSendToASP}
              isSubmitting={isSubmitting}
            />
          </div>
        </div>

        {/* Right: History */}
        <div className="flex flex-col gap-6 sticky top-20">
          {history.length > 0 && (
            <div className="bg-white border border-[#e3eaf7] rounded-xl p-5 shadow-sm">
              <h2 className="text-xs font-semibold text-[#8899b0] uppercase tracking-wider mb-3">Session Stats</h2>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { label: 'Total', val: history.length, cls: 'text-[#1a2340]' },
                  { label: 'Valid', val: history.filter(h => h.valid).length, cls: 'text-[#22c55e]' },
                  { label: 'Invalid', val: history.filter(h => !h.valid).length, cls: 'text-[#e53e3e]' },
                  {
                    label: 'Pass rate',
                    val: history.length ? Math.round(history.filter(h => h.valid).length / history.length * 100) + '%' : '–',
                    cls: 'text-[#1a6fcf]'
                  },
                ].map(s => (
                  <div key={s.label} className="bg-[#f8faff] rounded-lg p-3 text-center border border-[#e3eaf7]">
                    <div className={`text-xl font-bold ${s.cls}`}>{s.val}</div>
                    <div className="text-xs font-medium text-[#5a6a85] mt-1">{s.label}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="bg-white border border-[#e3eaf7] rounded-xl p-5 shadow-sm max-h-[500px] overflow-y-auto">
            <h2 className="text-sm font-semibold text-[#8899b0] uppercase tracking-wider mb-4">
              Session History
              {history.length > 0 && (
                <span className="ml-2 px-2 py-0.5 bg-[#e8f1ff] text-[#1a6fcf] rounded-full text-xs font-bold">
                  {history.length}
                </span>
              )}
            </h2>
            <SessionHistory
              history={history}
              onReload={setPayload}
            />
          </div>
        </div>

      </div>
    </div>
  )
}
