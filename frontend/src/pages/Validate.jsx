import { useState, useCallback, useEffect } from 'react'
import PayloadEditor from '../components/PayloadEditor'
import PipelineRunner from '../components/PipelineRunner'
import ValidationReport from '../components/ValidationReport'
import SessionHistory from '../components/SessionHistory'
import { useInvoiceApi } from '../hooks/useInvoiceApi'
import { SAMPLES, DEMO_API_KEY } from '../constants/samplePayloads'

const DEFAULT_PAYLOAD = JSON.stringify(SAMPLES.b2b.payload, null, 2)

export default function Validate() {
  const [payload, setPayload] = useState(DEFAULT_PAYLOAD)
  const [apiKey, setApiKey] = useState(DEMO_API_KEY)
  const [history, setHistory] = useState([])
  const [lastAddedTimestamp, setLastAddedTimestamp] = useState(null)

  const { stages, results, error, isRunning, runPipeline, runSingle, reset } = useInvoiceApi()

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
    await runSingle(endpoint, payload, apiKey)
  }

  const wrappedRunAll = async () => {
    reset()
    await runPipeline(payload, apiKey)
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

      <div className="grid grid-cols-1 xl:grid-cols-[1fr_1fr_300px] gap-6 items-start">
        
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
            />
          </div>
        </div>

        {/* Middle: Pipeline + Results */}
        <div className="flex flex-col gap-6">
          <div className="bg-white border border-[#e3eaf7] rounded-xl p-5 shadow-sm">
            <h2 className="text-sm font-semibold text-[#8899b0] uppercase tracking-wider mb-4">Pipeline</h2>
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
            <ValidationReport stages={stages} results={results} error={error} />
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
