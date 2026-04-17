import { useState, useEffect } from 'react'
import Card from '../components/ui/Card'
import Pill from '../components/ui/Pill'
import Button from '../components/ui/Button'
import { Search, Download, Filter, XCircle, CheckCircle } from 'lucide-react'
import { API_BASE } from '../constants/api'
import { downloadCsv, API_HEADERS } from '../constants/apiHelpers'
import DateRangeFilter from '../components/ui/DateRangeFilter'
import toast from 'react-hot-toast'
import { Send, RefreshCw } from 'lucide-react'

export default function History() {
  const [runs, setRuns] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('All')
  const [search, setSearch] = useState('')
  const [dateRange, setDateRange] = useState({ start: '', end: '' })

  useEffect(() => {
    const timer = setTimeout(async () => {
      try {
        setLoading(true)
        const params = new URLSearchParams()
        if (filter !== 'All') params.append('is_valid', filter === 'Valid' ? 'true' : 'false')
        if (search) params.append('search', search)
        if (dateRange.start && dateRange.end) {
          params.append('start_date', dateRange.start)
          params.append('end_date', dateRange.end)
        }
        
        const q = params.toString() ? `?${params.toString()}` : ''
        const res = await fetch(`${API_BASE}/api/v1/history${q}`, { 
          headers: API_HEADERS
        })
        const json = await res.json()
        setRuns(json.items || [])
      } catch (e) {
        console.error(e)
      } finally {
        setLoading(false)
      }
    }, 400) // Debounce search

    return () => clearTimeout(timer)
  }, [filter, search, dateRange])

  const handleExport = async () => {
    try {
      const params = new URLSearchParams()
      if (dateRange.start && dateRange.end) {
        params.append('start_date', dateRange.start)
        params.append('end_date', dateRange.end)
      }
      const q = params.toString() ? `?${params.toString()}` : ''
      await downloadCsv(`${API_BASE}/api/v1/export/csv${q}`, 'validation_history.csv')
      toast.success('CSV downloaded successfully')
    } catch (e) {
      toast.error(`Export failed: ${e.message}`)
    }
  }

  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSendSingleToASP = async (invoiceNumber) => {
    setIsSubmitting(true)
    const t = toast.loading(`Sending Invoice #${invoiceNumber} to ASP...`)
    try {
      const res = await fetch(`${API_BASE}/asp/v1/submit-validated?source_module=History%20Module&source_filename=history_export.json`, {
        method: 'POST',
        headers: API_HEADERS,
        body: JSON.stringify([invoiceNumber])
      })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      toast.success(`Invoice #${invoiceNumber} successfully sent to ASP Portal!`, { id: t })
    } catch (e) {
      toast.error(`ASP Submission failed: ${e.message}`, { id: t })
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[#1a2340]">Validation History</h1>
          <p className="text-sm text-[#5a6a85] mt-1">Full audit log of all system runs</p>
        </div>
        <div className="flex gap-2">
          <Button variant="ghost" onClick={handleExport}>
            <Download className="w-4 h-4 mr-2" />
            Export CSV
          </Button>
          <Button variant="primary">Bulk Resubmit</Button>
        </div>
      </div>

      <Card className="flex flex-col">
        <div className="p-4 border-b border-[#e3eaf7] flex flex-wrap gap-4 items-center justify-between">
          <div className="flex items-center gap-2 flex-1 min-w-[200px] max-w-md">
            <div className="relative w-full">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[#8899b0]" />
              <input 
                type="text" 
                placeholder="Search invoice number, type..." 
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-9 pr-4 py-2 text-sm border border-[#e3eaf7] rounded-lg focus:outline-none focus:border-[#1a6fcf] focus:ring-1 focus:ring-[#1a6fcf]"
              />
            </div>
          </div>
          <div className="flex items-center gap-1 bg-[#f8faff] p-1 rounded-lg border border-[#e3eaf7]">
            {['All', 'Valid', 'Invalid'].map(f => (
              <button 
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                  filter === f ? 'bg-white shadow-sm text-[#1a2340] cursor-default' : 'text-[#8899b0] hover:text-[#5a6a85]'
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>
        <div className="px-4 pb-4 border-b border-[#e3eaf7] bg-[#f8faff]/50">
           <DateRangeFilter 
             onChange={(range) => setDateRange(range)}
             initialStart={dateRange.start}
             initialEnd={dateRange.end}
           />
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm whitespace-nowrap">
            <thead className="bg-[#f8faff] text-[#5a6a85]">
              <tr>
                <th className="px-6 py-3 font-medium">Invoice Number</th>
                <th className="px-6 py-3 font-medium">Date & Time</th>
                <th className="px-6 py-3 font-medium">Type</th>
                <th className="px-6 py-3 font-medium">Status</th>
                <th className="px-6 py-3 font-medium">Errors</th>
                <th className="px-6 py-3 font-medium">Pass %</th>
                <th className="px-6 py-3 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#e3eaf7]">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-[#8899b0]">Loading history...</td>
                </tr>
              ) : runs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-[#8899b0]">No runs match your filter.</td>
                </tr>
              ) : runs.map((run, i) => (
                <tr key={i} className="hover:bg-[#f8faff] cursor-pointer">
                  <td className="px-6 py-4 font-mono font-medium text-[#1a6fcf]">{run.invoice_number || 'UNKNOWN'}</td>
                  <td className="px-6 py-4 text-[#5a6a85]">{new Date(run.created_at).toLocaleString()}</td>
                  <td className="px-6 py-4">
                    <Pill variant={run.transaction_type?.includes('Credit') ? 'violet' : run.transaction_type?.includes('B2C') ? 'teal' : 'blue'}>
                      {run.transaction_type || 'Unknown'}
                    </Pill>
                  </td>
                  <td className="px-6 py-4">
                    <Pill variant={run.is_valid ? 'green' : 'red'}>
                      {run.is_valid ? 'VALID' : 'INVALID'}
                    </Pill>
                  </td>
                  <td className="px-6 py-4 font-medium text-[#1a2340]">
                    {run.total_errors > 0 ? (
                      <span className="text-[#e53e3e] flex items-center gap-1">
                        <XCircle className="w-4 h-4" /> {run.total_errors} errors
                      </span>
                    ) : (
                      <span className="text-[#22c55e] flex items-center gap-1">
                        <CheckCircle className="w-4 h-4" /> None
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 font-semibold text-[#1a2340]">
                    {run.pass_percentage ?? 100}%
                  </td>
                  <td className="px-6 py-4 text-right">
                    {run.is_valid && (
                      <button 
                        onClick={(e) => { e.stopPropagation(); handleSendSingleToASP(run.invoice_number); }}
                        disabled={isSubmitting}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#f0f7ff] text-[#1a6fcf] rounded-lg text-xs font-bold hover:bg-[#1a6fcf] hover:text-white transition-all shadow-sm"
                      >
                        {isSubmitting ? <RefreshCw className="w-3 h-3 animate-spin" /> : <Send className="w-3 h-3" />}
                        Send to ASP
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}
