import { useState, useRef } from 'react'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Pill from '../components/ui/Pill'
import ProgressBar from '../components/ui/ProgressBar'
import { Upload, FileDown, RefreshCw, AlertCircle, CheckCircle, Send } from 'lucide-react'
import toast from 'react-hot-toast'
import { API_BASE } from '../constants/api'
import { API_HEADERS } from '../constants/apiHelpers'

export default function BulkUpload() {
  const [file, setFile] = useState(null)
  const [isDragActive, setIsDragActive] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(null)
  const [results, setResults] = useState([])
  const [fullPipeline, setFullPipeline] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const fileInputRef = useRef(null)

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') setIsDragActive(true)
    else if (e.type === 'dragleave') setIsDragActive(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0])
    }
  }

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0])
    }
  }

  const validateAndSetFile = (f) => {
    if (f.name.match(/\.(xlsx|xls|csv|xml|zip)$/i)) {
      setFile(f)
      setResults([]) // Reset previous results
    } else {
      alert('Supported formats: .xlsx, .csv, .xml, .zip')
    }
  }

  const pollStatus = (batchId) => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/api/v1/batch-status/${batchId}`, { 
          headers: API_HEADERS
        })
        if (res.ok) {
          const data = await res.json()
          setProgress(data)
          if (data.status === 'COMPLETE') {
            clearInterval(interval)
            setUploading(false)
            setResults(data.results || [])
          }
        } else if (res.status === 404) {
          // May take a bit to register
        }
      } catch (e) {
        console.error(e)
      }
    }, 2000)
  }

  const submit = async () => {
    if (!file) return
    setUploading(true)
    setProgress({ status: 'UPLOADING', total: 0, done: 0 })
    try {
      const form = new FormData()
      form.append('file', file)
      
      // We must NOT set Content-Type header when sending FormData, 
      // let the browser set it with the correct boundary.
      const { 'Content-Type': _, ...headersWithoutContentType } = API_HEADERS;

      const res = await fetch(`${API_BASE}/api/v1/ingest-bulk?full_pipeline=${fullPipeline}`, {
        method: 'POST',
        headers: headersWithoutContentType,
        body: form
      })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      pollStatus(data.batch_id)
    } catch (e) {
      console.error(e)
      setUploading(false)
      alert("Upload failed: " + e.message)
    }
  }

  const dlTemplate = async () => {
    // Hits the backend with security header and downloads as blob
    try {
      const res = await fetch(`${API_BASE}/api/v1/download-template`, {
        headers: API_HEADERS
      })
      if (!res.ok) throw new Error("Failed to download")
      
      const blob = await res.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = "PINT_AE_Bulk_Template.xlsx"
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (e) {
      alert("Template download failed: " + e.message)
    }
  }

  const calcPercentage = () => {
    if (!progress || !progress.total) return 0
    return Math.round((progress.done / progress.total) * 100)
  }

  function cleanError(rawError) {
    if (!rawError) return ''
    if (rawError.includes('string_type')) {
      const field = rawError.match(/(\w+)\s+Input should be a valid string/)?.[1] || 'field'
      return `${field}: value must be text — re-download template`
    }
    if (rawError.includes('missing')) {
      const field = rawError.match(/(\w+)\s+Field required/)?.[1] || 'field'
      return `${field}: required field is missing`
    }
    return rawError.split('For further information')[0].trim()
  }

  const resubmitFailed = async () => {
    const failedOnes = results.filter(r => !r.is_valid && r.raw_payload)
    if (failedOnes.length === 0) return

    setUploading(true)
    setProgress({ status: 'RESUBMITTING', total: failedOnes.length, done: 0 })

    try {
      // Ensure we only send valid payloads
      const payloads = failedOnes.map(f => f.raw_payload)
      
      const res = await fetch(`${API_BASE}/api/v1/batch-validate?full_pipeline=${fullPipeline}`, {
        method: 'POST',
        headers: API_HEADERS,
        body: JSON.stringify(payloads)
      })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      pollStatus(data.batch_id)
    } catch (e) {
      console.error(e)
      setUploading(false)
      alert("Resubmit failed: " + e.message)
    }
  }

  const hasFailures = results.some(r => !r.is_valid)
  const validResultsCount = results.filter(r => r.is_valid && r.raw_payload).length

  const handleSendToASP = async () => {
    const validOnes = results.filter(r => r.is_valid);
    if (validOnes.length === 0) return toast.error("No valid invoices to send.");

    setIsSubmitting(true);
    const t = toast.loading(`Initiating ASP/FTA submission for ${validOnes.length} invoices...`);
    try {
      const invoiceNumbers = validOnes.map(v => v.invoice_number);
      
      const res = await fetch(`${API_BASE}/asp/v1/submit-validated?source_module=Bulk%20Upload&source_filename=${encodeURIComponent(file?.name || 'bulk_upload.xlsx')}`, {
        method: 'POST',
        headers: API_HEADERS,
        body: JSON.stringify(invoiceNumbers)
      });
      
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      
      toast.success(`Successfully sent ${data.submitted} invoices to ASP! Logs available in ASP Portal.`, { 
        id: t,
        duration: 5000
      });
      
    } catch (e) {
      console.error(e);
      toast.error("ASP Submission failed: " + e.message, { id: t });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[#1a2340]">Bulk Upload & Validate</h1>
          <p className="text-sm text-[#5a6a85] mt-1">Ingest multiple invoices via Excel, CSV, XML, or Zip</p>
        </div>
        <Button variant="ghost" onClick={dlTemplate}>
          <FileDown className="w-4 h-4 mr-2" />
          Download Template
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_2fr] gap-6">
        <Card className="p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-[#1a2340]">Upload File</h2>
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
          <div 
            className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors ${
              isDragActive ? 'border-[#1a6fcf] bg-[#e8f1ff]' : 'border-[#e3eaf7] hover:border-[#8899b0] hover:bg-[#f8faff]'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input 
              type="file" 
              ref={fileInputRef} 
              onChange={handleFileChange} 
              accept=".xlsx,.xls,.csv,.xml,.zip" 
              className="hidden" 
            />
            <div className="w-12 h-12 rounded-full bg-[#f8faff] text-[#1a6fcf] mx-auto flex items-center justify-center mb-4 border border-[#e3eaf7]">
              <Upload className="w-6 h-6" />
            </div>
            {file ? (
              <div className="text-sm font-medium text-[#1a2340] break-words">
                {file.name} ({(file.size / 1024).toFixed(1)} KB)
              </div>
            ) : (
              <>
                <p className="text-sm font-medium text-[#1a2340] mb-1">Click or drag file to this area</p>
                <p className="text-xs text-[#8899b0]">Supports .XLSX, .CSV, .XML and .ZIP up to 50MB</p>
              </>
            )}
          </div>
          
          <Button 
            className="w-full mt-6" 
            disabled={!file || uploading} 
            onClick={submit}
          >
            {uploading ? (
              <>
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                Processing...
              </>
            ) : 'Start Validation'}
          </Button>

          {progress && (
            <div className="mt-6 p-4 bg-[#f8faff] border border-[#e3eaf7] rounded-lg">
              <div className="flex justify-between text-xs font-semibold text-[#5a6a85] uppercase tracking-wider mb-2">
                <span>{progress.status}</span>
                <span>{calcPercentage()}%</span>
              </div>
              <ProgressBar progress={calcPercentage()} />
              {progress.total > 0 && (
                <div className="text-xs text-[#5a6a85] text-center mt-2">
                  Processed {progress.done} of {progress.total} invoices
                </div>
              )}
            </div>
          )}
        </Card>

        <Card className="flex flex-col">
          <div className="p-4 border-b border-[#e3eaf7] flex justify-between items-center">
            <h2 className="text-lg font-semibold text-[#1a2340]">Validation Results</h2>
            <div className="flex gap-2 ml-auto">
              {validResultsCount > 0 && !uploading && (
                <Button 
                  variant="primary" 
                  disabled={isSubmitting} 
                  onClick={handleSendToASP}
                  className="bg-[#1a2340] hover:bg-[#111827] border-none shadow-lg transform active:scale-95 transition-all px-6"
                >
                  {isSubmitting ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Send className="w-4 h-4 mr-2" />}
                  Send {validResultsCount} Invoices to ASP Portal
                </Button>
              )}
              {hasFailures && !uploading && (
                <Button variant="danger" className="animate-pulse" onClick={resubmitFailed}>
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Resubmit Failed Rows
                </Button>
              )}
            </div>
          </div>
          <div className="flex-1 overflow-x-auto min-h-[300px]">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="bg-[#f8faff] text-[#5a6a85]">
                <tr>
                  <th className="px-6 py-3 font-medium">Row</th>
                  <th className="px-6 py-3 font-medium">Invoice Number</th>
                  <th className="px-6 py-3 font-medium">Status</th>
                  <th className="px-6 py-3 font-medium w-full">Error Summary</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#e3eaf7]">
                {results.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-6 py-12 text-center text-[#8899b0]">
                      <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-[#f8faff] text-[#8899b0] mb-4">
                        <CheckCircle className="w-6 h-6" />
                      </div>
                      <p>Run a batch upload to see results</p>
                    </td>
                  </tr>
                ) : results.map((r, i) => (
                  <tr key={i} className="hover:bg-[#f8faff] group">
                    <td className="px-6 py-3 font-mono text-[#8899b0]">{i + 1}</td>
                    <td className="px-6 py-3 font-medium text-[#1a2340]">
                      {r.invoice_number && r.invoice_number !== 'Unknown' ? r.invoice_number : `Row #${i+1}`}
                    </td>
                    <td className="px-6 py-3">
                      <Pill variant={r.is_valid ? 'green' : 'red'}>
                        {r.is_valid ? 'PASSED' : 'FAILED'}
                      </Pill>
                    </td>
                    <td className="px-6 py-3 whitespace-normal">
                      {r.is_valid ? (
                        <span className="text-[#5a6a85] text-xs">Ready for FTA submission</span>
                      ) : (
                        <div className="flex flex-col gap-1">
                          {(r.errors || []).map((err, j) => (
                            <div key={j} className="text-xs text-[#e53e3e] flex items-start gap-1">
                              <AlertCircle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
                              <span><b>{err.field}</b>: {cleanError(err.message || err.error)}</span>
                            </div>
                          ))}
                          {r.error && <div className="text-xs text-[#e53e3e]">{cleanError(r.error)}</div>}
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </div>
  )
}
