import React, { useState, useEffect } from 'react'
import Card from '../components/ui/Card'
import Pill from '../components/ui/Pill'
import Button from '../components/ui/Button'
import { 
  Search, Download, FileJson, Clock, CheckCircle2, XCircle, 
  AlertCircle, ShieldCheck, Database, HardDrive, RefreshCw,
  ExternalLink, FileText, Info
} from 'lucide-react'
import axios from 'axios'
import toast from 'react-hot-toast'
import { useAuth } from '../context/AuthContext'
import { getApiHeaders } from '../constants/apiHelpers'
import DateRangeFilter from '../components/ui/DateRangeFilter'

const API_BASE = '/api/v1/audit'

export default function AuditPortal() {
  const { token } = useAuth()
  const [submissions, setSubmissions] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('All')
  const [dateRange, setDateRange] = useState({ start: '', end: '' })
  const client_id = "demo-client-phase2"

  useEffect(() => {
    fetchSubmissions()
  }, [statusFilter, dateRange])

  const fetchSubmissions = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      params.append('client_id', client_id)
      if (statusFilter !== 'All') params.append('status', statusFilter === 'Valid' ? 'Accepted' : 'Rejected')
      if (dateRange.start) params.append('start_date', dateRange.start)
      if (dateRange.end) params.append('end_date', dateRange.end)

      const res = await axios.get(`${API_BASE}/submissions?${params.toString()}`, {
        headers: getApiHeaders(token)
      })
      setSubmissions(res.data.items)
    } catch (err) {
      toast.error("Failed to load enterprise audit logs")
    } finally {
      setLoading(false)
    }
  }

  const downloadRaw = async (submissionId) => {
    const t = toast.loading("Fetching secure payload...")
    try {
      // Explicitly request the "request" payload which contains the UBL XML invoice
      const res = await axios.get(`${API_BASE}/raw-payload?client_id=${client_id}&submission_id=${submissionId}&doc_type=request`, {
        responseType: 'blob',
        headers: getApiHeaders(token)
      })
      
      // Extract filename and content type
      const contentType = res.headers['content-type']
      const contentDisposition = res.headers['content-disposition']
      const customFilename = res.headers['x-file-name']
      
      let extension = 'xml'
      if (contentType === 'application/xml' || contentType === 'text/xml') extension = 'xml'
      if (contentType === 'application/json') extension = 'json'
      
      let filename = customFilename || `ASP_REQUEST_${submissionId.slice(0, 8)}.${extension}` 
      
      if (contentDisposition) {
        const match = contentDisposition.match(/filename="?([^"]+)"?/)
        if (match && match[1]) filename = match[1]
      }

      const url = window.URL.createObjectURL(new Blob([res.data], { type: contentType }))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      toast.success("Evidence downloaded", { id: t })
    } catch (err) {
      console.error("Payload retrieval error:", err)
      toast.error("File retrieval failed: " + (err.response?.data?.detail || "Connection Error"), { id: t })
    }
  }

  const filteredSubmissions = submissions.filter(s => {
    // Search Query (Status and Date are now handled at backend)
    const query = searchQuery.toLowerCase()
    return (
      s.invoice_number.toLowerCase().includes(query) ||
      s.submission_id.toLowerCase().includes(query) ||
      (s.source_filename && s.source_filename.toLowerCase().includes(query))
    )
  })

  const stats = {
    total: submissions.length,
    accepted: submissions.filter(s => s.status === 'Accepted').length,
    rejected: submissions.filter(s => s.status !== 'Accepted').length,
    avgLatency: submissions.length 
      ? Math.round(submissions.reduce((acc, s) => acc + (s.response_time_ms || 240), 0) / submissions.length) 
      : 0
  }

  return (
    <div className="p-8 max-w-[1600px] mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      
      {/* Header & Stats Section */}
      <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-6">
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-[#1a6fcf] font-bold text-xs uppercase tracking-[0.2em]">
            <ShieldCheck size={16} /> Regulatory Compliance Layer
          </div>
          <h1 className="text-4xl font-black text-[#1a2340] tracking-tight">ASP Integration Portal</h1>
          <p className="text-[#5a6a85] text-lg font-medium">Real-time audit trail for all FTA gateway communications</p>
        </div>
        
        <div className="flex flex-wrap gap-4">
          {[
            { label: 'Cloud Status', val: 'Operational', color: 'text-emerald-500', icon: Database },
            { label: 'Avg Latency', val: `${stats.avgLatency}ms`, color: 'text-[#1a6fcf]', icon: Clock },
            { label: 'Success Rate', val: stats.total ? Math.round((stats.accepted / stats.total) * 100) + '%' : '100%', color: 'text-amber-500', icon: CheckCircle2 },
          ].map(s => (
            <div key={s.label} className="bg-white px-6 py-4 rounded-2xl border border-[#e3eaf7] shadow-sm flex items-center gap-4">
              <div className={`p-3 rounded-xl bg-slate-50 ${s.color}`}>
                <s.icon size={20} />
              </div>
              <div>
                <div className="text-[10px] font-bold text-[#8899b0] uppercase tracking-wider">{s.label}</div>
                <div className={`text-lg font-black ${s.color}`}>{s.val}</div>
              </div>
            </div>
          ))}
          <Button onClick={fetchSubmissions} variant="primary" className="h-full px-8 rounded-2xl shadow-lg shadow-[#1a6fcf]/20">
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} /> Refresh Portal
          </Button>
        </div>
      </div>

      {/* Search & Filter Bar */}
      <div className="space-y-4">
        <div className="flex flex-col md:flex-row gap-6 items-center">
          {/* Status Tabs (Run History Style) */}
          <div className="flex items-center gap-1 bg-white p-1.5 rounded-2xl border border-[#e3eaf7] shadow-sm">
            {['All', 'Valid', 'Invalid'].map(f => (
              <button 
                key={f}
                onClick={() => setStatusFilter(f)}
                className={`px-6 py-2 text-sm font-bold rounded-xl transition-all ${
                  statusFilter === f 
                    ? 'bg-[#1a2340] text-white shadow-lg' 
                    : 'text-[#8899b0] hover:text-[#5a6a85] hover:bg-slate-50'
                }`}
              >
                {f}
              </button>
            ))}
          </div>

          <div className="relative flex-1 group w-full">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-[#8899b0] group-focus-within:text-[#1a6fcf] transition-colors" size={20} />
            <input 
              type="text" 
              placeholder="Search by Invoice #, Submission ID, or Filename..." 
              className="w-full h-12 pl-12 pr-6 py-2 bg-white border border-[#e3eaf7] rounded-2xl shadow-sm focus:outline-none focus:ring-4 focus:ring-[#1a6fcf]/5 focus:border-[#1a6fcf] transition-all text-sm font-medium"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>

        <div className="flex justify-end">
           <DateRangeFilter 
             onChange={(range) => setDateRange(range)}
             initialStart={dateRange.start}
             initialEnd={dateRange.end}
           />
        </div>
      </div>

      {/* Main Data Grid */}
      <Card className="rounded-[2rem] border-[#e3eaf7] overflow-hidden shadow-2xl relative">
        {loading && (
          <div className="absolute inset-0 bg-white/60 backdrop-blur-sm z-50 flex flex-col items-center justify-center">
            <div className="w-12 h-12 border-4 border-[#1a6fcf] border-t-transparent rounded-full animate-spin mb-4" />
            <span className="text-sm font-bold text-[#1a2340] animate-pulse">Synchronizing with ASP Gateway...</span>
          </div>
        )}
        
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm border-collapse">
            <thead>
              <tr className="bg-[#f8faff] text-[#5a6a85] border-b border-[#e3eaf7]">
                <th className="px-8 py-5 font-black uppercase text-[10px] tracking-widest">Processing Details</th>
                <th className="px-8 py-5 font-black uppercase text-[10px] tracking-widest">Invoice Node</th>
                <th className="px-8 py-5 font-black uppercase text-[10px] tracking-widest">ASP Status</th>
                <th className="px-8 py-5 font-black uppercase text-[10px] tracking-widest text-center">Protocol</th>
                <th className="px-8 py-5 font-black uppercase text-[10px] tracking-widest text-center">Validation</th>
                <th className="px-8 py-5 font-black uppercase text-[10px] tracking-widest">Ingestion Source</th>
                <th className="px-8 py-5 font-black uppercase text-[10px] tracking-widest text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#e3eaf7]">
              {filteredSubmissions.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-8 py-20 text-center">
                    <div className="flex flex-col items-center gap-4 max-w-sm mx-auto">
                       <div className="w-20 h-20 rounded-full bg-slate-50 flex items-center justify-center border border-[#e3eaf7]">
                          <Database className="w-10 h-10 text-[#cbd5e1]" />
                       </div>
                       <div>
                         <h3 className="text-lg font-bold text-[#1a2340]">No Handshakes Found</h3>
                         <p className="text-sm text-[#8899b0]">Your regulatory logs are clean. Start by validating an invoice or performing a bulk upload.</p>
                       </div>
                    </div>
                  </td>
                </tr>
              ) : filteredSubmissions.map(sub => (
                <tr key={sub.submission_id} className="hover:bg-[#fcfdfe] transition-all group">
                  <td className="px-8 py-6">
                    <div className="flex flex-col gap-1">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-[11px] text-[#1a6fcf] bg-[#f0f7ff] px-2 py-0.5 rounded-md font-bold">
                          UID: {sub.submission_id.slice(0, 14)}
                        </span>
                        <Info size={12} className="text-[#8899b0] opacity-0 group-hover:opacity-100 transition-opacity cursor-help" />
                      </div>
                      <span className="text-[10px] text-[#8899b0] font-medium italic">Handshake ID: {sub.submission_id}</span>
                    </div>
                  </td>
                  <td className="px-8 py-6">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-slate-50 flex items-center justify-center border border-[#e3eaf7] text-[#1a2340]">
                        <FileText size={18} />
                      </div>
                      <div className="flex flex-col">
                        <span className="font-black text-[#1a2340] text-base">{sub.invoice_number}</span>
                        <span className="text-[10px] text-[#5a6a85] font-bold uppercase">{new Date(sub.timestamp).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })}</span>
                      </div>
                    </div>
                  </td>
                  <td className="px-8 py-6">
                    <div className="flex flex-col gap-1.5">
                      <Pill variant={sub.status === 'Accepted' ? 'green' : 'red'} className="w-fit px-3 py-1 text-[10px] font-black uppercase tracking-widest">
                        {sub.status}
                      </Pill>
                      {sub.status === 'Accepted' ? (
                        <div className="flex items-center gap-1 text-[10px] text-emerald-600 font-bold">
                           <ShieldCheck size={10} /> Validated & Signed
                        </div>
                      ) : (
                        <div className="flex items-center gap-1 text-[10px] text-red-600 font-bold">
                           <AlertCircle size={10} /> Rejected by Gateway
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="px-8 py-6 text-center">
                    <div className="flex flex-col">
                      <span className={`text-sm font-black ${sub.http_status === 200 ? 'text-[#22c55e]' : 'text-[#e53e3e]'}`}>
                        HTTP {sub.http_status}
                      </span>
                      <span className="text-[10px] text-[#8899b0] font-bold">REST/JSON</span>
                    </div>
                  </td>
                  <td className="px-8 py-6 text-center">
                    {sub.error_count > 0 ? (
                       <div className="inline-flex flex-col items-center">
                          <div className="flex items-center gap-1.5 text-[#e53e3e] font-black underline underline-offset-4 decoration-red-200">
                             <XCircle size={14} /> {sub.error_count} ERRORS
                          </div>
                          <span className="text-[9px] text-[#8899b0] font-bold mt-1 uppercase">PINT AE Ruleset</span>
                       </div>
                    ) : (
                       <div className="inline-flex flex-col items-center">
                          <div className="flex items-center gap-1.5 text-emerald-500 font-black">
                             <CheckCircle2 size={16} /> 100% PASS
                          </div>
                          <span className="text-[9px] text-emerald-600/60 font-black mt-1 uppercase tracking-tighter">Compliant</span>
                       </div>
                    )}
                  </td>
                  <td className="px-8 py-6">
                     <div className="flex flex-col gap-1">
                       <div className="flex items-center gap-1.5">
                         <HardDrive size={12} className="text-[#1a2340]" />
                         <span className="text-[11px] font-black text-[#1a2340] uppercase tracking-tight">{sub.source_module || 'Manual Entry'}</span>
                       </div>
                       {sub.source_filename && (
                         <div className="flex items-center gap-1 text-[10px] text-[#8899b0] bg-slate-50 px-2 py-0.5 rounded border border-[#e3eaf7] w-fit max-w-[150px] truncate">
                           {sub.source_filename}
                         </div>
                       )}
                     </div>
                   </td>
                  <td className="px-8 py-6 text-right">
                    <button 
                      onClick={() => downloadRaw(sub.submission_id)}
                      className="inline-flex items-center gap-2 px-5 py-2.5 bg-[#f0f7ff] text-[#1a6fcf] rounded-xl text-xs font-black hover:bg-[#1a6fcf] hover:text-white transition-all shadow-sm hover:shadow-lg hover:shadow-[#1a6fcf]/20 active:scale-95 group/btn"
                    >
                      <FileText className="w-4 h-4" /> 
                      <span>FILE</span>
                      <Download size={12} className="opacity-40 group-hover/btn:translate-y-0.5 transition-transform" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <div className="flex flex-col md:flex-row items-center justify-between p-8 bg-[#1a2340] rounded-[2rem] text-white overflow-hidden relative shadow-xl">
         <div className="absolute right-0 top-0 w-64 h-64 bg-[#1a6fcf] opacity-10 rounded-full -mr-32 -mt-32 blur-3xl" />
         <div className="relative flex items-center gap-6">
            <div className="p-4 bg-white/10 rounded-2xl backdrop-blur-md">
               <ShieldCheck size={32} className="text-emerald-400" />
            </div>
            <div>
               <h4 className="text-xl font-black tracking-tight">System Integrity Verified</h4>
               <p className="text-sm text-slate-300 font-medium">Currently connected to UAE-ASP-GATEWAY-MOCK v4.2.1-stable</p>
            </div>
         </div>
         <div className="relative mt-6 md:mt-0 flex gap-10">
            <div className="text-center">
              <div className="text-2xl font-black text-emerald-400">{submissions.length}</div>
              <div className="text-[10px] font-black uppercase tracking-widest text-slate-400">Total Logs</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-black text-emerald-400">99.9%</div>
              <div className="text-[10px] font-black uppercase tracking-widest text-slate-400">Uptime</div>
            </div>
            <div className="text-center border-l border-white/10 pl-10">
              <div className="text-lg font-bold">AWS S3 Tier</div>
              <div className="text-[10px] font-black uppercase tracking-widest text-emerald-400">Storage Layer</div>
            </div>
         </div>
      </div>
    </div>
  )
}
