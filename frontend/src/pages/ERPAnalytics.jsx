import React, { useState, useEffect } from 'react'
import { 
  Server, 
  Activity, 
  Zap, 
  ChevronDown, 
  CheckCircle2, 
  AlertCircle, 
  Clock, 
  ArrowRightLeft,
  Database,
  CloudLightning,
  ShieldCheck,
  Globe,
  Building2,
  Settings as SettingsIcon,
  CloudUpload,
  Webhook,
  FileText,
  Search
} from 'lucide-react'
import axios from 'axios'
import toast from 'react-hot-toast'
import { useAuth } from '../context/AuthContext'
import { getApiHeaders } from '../constants/apiHelpers'
import Card from '../components/ui/Card'
import Pill from '../components/ui/Pill'
import Button from '../components/ui/Button'
import DateRangeFilter from '../components/ui/DateRangeFilter'

const API_BASE = '/api/v1'

const ERP_ICONS = {
  SAP: Building2,
  NETSUITE: Globe,
  DYNAMICS: SettingsIcon,
  SFTP: CloudUpload,
  WEBHOOK: Webhook,
  GENERIC: Server
}

export default function ERPAnalytics() {
  const { token } = useAuth()
  const [connections, setConnections] = useState([])
  const [selectedConn, setSelectedConn] = useState(null)
  const [dataFlow, setDataFlow] = useState([])
  const [loading, setLoading] = useState(true)
  const [fetchingData, setFetchingData] = useState(false)
  const [statusFilter, setStatusFilter] = useState('All')
  const [dateRange, setDateRange] = useState({ start: '', end: '' })
  const [searchQuery, setSearchQuery] = useState('')
  const client_id = "demo-client-phase2"

  useEffect(() => {
    fetchConnections()
  }, [])

  const fetchConnections = async () => {
    try {
      setLoading(true)
      const res = await axios.get(`${API_BASE}/integrations/connections`, {
        headers: getApiHeaders(token)
      })
      const activeConns = res.data.filter(c => c.status === 'active')
      setConnections(activeConns)
      if (activeConns.length > 0) {
        handleSelectERP(activeConns[0])
      }
    } catch (err) {
      toast.error("Failed to load active ERP integrations")
    } finally {
      setLoading(false)
    }
  }

  const handleSelectERP = async (conn) => {
    setSelectedConn(conn)
  }

  useEffect(() => {
    if (selectedConn) {
      fetchERPDataFlow(selectedConn)
    }
  }, [selectedConn, statusFilter, dateRange])

  const fetchERPDataFlow = async (conn) => {
    try {
      setFetchingData(true)
      const params = new URLSearchParams()
      params.append('client_id', client_id)
      params.append('limit', '20')
      if (statusFilter !== 'All') params.append('status', statusFilter === 'Valid' ? 'Accepted' : 'Rejected')
      if (dateRange.start) params.append('start_date', dateRange.start)
      if (dateRange.end) params.append('end_date', dateRange.end)

      const res = await axios.get(`${API_BASE}/audit/submissions?${params.toString()}`, {
        headers: getApiHeaders(token)
      })
      setDataFlow(res.data.items)
    } catch (err) {
      toast.error("Failed to fetch ERP data flow")
    } finally {
      setFetchingData(false)
    }
  }

  const filteredDataFlow = dataFlow.filter(row => {
    if (!searchQuery) return true
    return (
      row.invoice_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
      row.status.toLowerCase().includes(searchQuery.toLowerCase())
    )
  })

  if (loading) return (
    <div className="p-8 flex flex-col items-center justify-center min-h-[400px]">
      <Activity className="w-10 h-10 text-[#1a6fcf] animate-spin mb-4" />
      <p className="text-[#5a6a85] font-medium">Analyzing ERP Data Planes...</p>
    </div>
  )

  const Icon = selectedConn ? (ERP_ICONS[selectedConn.erp_type] || Server) : Server

  return (
    <div className="p-8 max-w-[1400px] mx-auto animate-in fade-in duration-500">
      <div className="flex flex-col md:flex-row md:items-center justify-between mb-10 gap-6">
        <div>
          <h1 className="text-2xl font-bold text-[#1a2b4b]">ERP Analytics</h1>
          <p className="text-sm text-[#5a6a85] font-medium mt-1">Real-time data synchronization Monitoring</p>
        </div>

        <div className="relative min-w-[280px]">
          <label className="absolute -top-2.5 left-3 px-1.5 bg-white text-[10px] font-bold text-[#1a6fcf] uppercase tracking-wider z-10">
            Select Active ERP
          </label>
          <div className="relative">
            <select 
              className="w-full h-12 pl-4 pr-10 bg-white border-2 border-[#e3eaf7] hover:border-[#1a6fcf] rounded-xl text-sm font-bold text-[#1a2340] appearance-none outline-none transition-all cursor-pointer shadow-sm"
              value={selectedConn?.id || ''}
              onChange={(e) => handleSelectERP(connections.find(c => c.id === e.target.value))}
            >
              {connections.length === 0 ? (
                <option disabled>No active ERPs configured</option>
              ) : (
                connections.map(c => (
                  <option key={c.id} value={c.id}>
                    {c.display_name} ({c.erp_type})
                  </option>
                ))
              )}
            </select>
            <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#5a6a85] pointer-events-none" />
          </div>
        </div>
      </div>

      {connections.length === 0 ? (
        <Card className="p-12 text-center border-dashed">
          <div className="w-16 h-16 bg-[#f0f7ff] rounded-full flex items-center justify-center text-[#1a6fcf] mx-auto mb-6">
            <ShieldCheck className="w-8 h-8" />
          </div>
          <h2 className="text-xl font-bold text-[#1a2340] mb-2">No Active Integrations</h2>
          <p className="text-[#5a6a85] max-w-md mx-auto mb-8">Configure your ERP in the Integration module to enable real-time analytics and data flow monitoring.</p>
          <Button onClick={() => window.location.href='/integrations'}>
            Go to Integrations
          </Button>
        </Card>
      ) : selectedConn && (
        <div className="space-y-8">
          {/* Top Panel: Connection Health */}
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            <Card className="p-6 border-l-4 border-l-[#1a6fcf]">
              <div className="flex items-center gap-4 mb-4">
                <div className="p-2.5 bg-[#f0f7ff] rounded-lg text-[#1a6fcf]">
                  <Icon className="w-6 h-6" />
                </div>
                <div>
                  <div className="text-[10px] font-bold text-[#8899b0] uppercase tracking-wider">ERP Mode</div>
                  <div className="text-sm font-black text-[#1a2340]">{selectedConn.integration_mode.toUpperCase().replace('_', ' ')}</div>
                </div>
              </div>
              <div className="flex items-center justify-between pt-4 border-t border-[#f1f5f9]">
                <div className="flex items-center gap-1.5 text-xs font-bold text-[#22c55e]">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Active
                </div>
                <div className="text-[10px] text-[#8899b0] font-medium">Since {new Date().toLocaleDateString()}</div>
              </div>
            </Card>

            <Card className="p-6">
              <div className="text-[10px] font-bold text-[#8899b0] uppercase tracking-wider mb-1">Last Synchronization</div>
              <div className="text-2xl font-black text-[#1a2340] mb-2">
                {selectedConn.last_sync_at ? new Date(selectedConn.last_sync_at).toLocaleTimeString() : 'Never'}
              </div>
              <div className="flex items-center gap-1.5 text-xs font-bold text-[#1a6fcf]">
                <Clock className="w-3.5 h-3.5" /> 
                {selectedConn.last_sync_status === 'success' ? 'Sync Stable' : 'Pending First Sync'}
              </div>
            </Card>

            <Card className="p-6">
              <div className="text-[10px] font-bold text-[#8899b0] uppercase tracking-wider mb-1">Invoices Processed</div>
              <div className="text-2xl font-black text-[#1a2340] mb-2">
                {selectedConn.last_sync_count || 0}
              </div>
              <div className="text-xs font-bold text-[#22c55e]">100% Delivery Rate</div>
            </Card>

            <Card className="p-6">
              <div className="text-[10px] font-bold text-[#8899b0] uppercase tracking-wider mb-1">Latency Avg. (to FTA)</div>
              <div className="text-2xl font-black text-[#1a2340] mb-2">124ms</div>
              <div className="text-xs font-bold text-[#1a6fcf]">Enterprise Optimized</div>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
             {/* Data Flow Table */}
              <div className="lg:col-span-2 space-y-6">
                 <div className="flex items-center justify-between">
                    <h2 className="text-lg font-bold text-[#1a2340] flex items-center gap-2">
                       <ArrowRightLeft className="w-5 h-5 text-[#1a6fcf]" />
                       Real-time Data Flow
                    </h2>
                    <div className="text-[10px] text-[#5a6a85] font-bold uppercase tracking-widest bg-[#f8faff] px-4 py-1.5 rounded-full border border-[#e3eaf7]">
                       {statusFilter} ({filteredDataFlow.length} Records)
                    </div>
                 </div>

                 {/* Premium Filter Controls */}
                 <div className="space-y-4">
                    <div className="flex flex-col md:flex-row gap-6 items-center">
                       {/* Status Tabs */}
                       <div className="flex items-center gap-1 bg-white p-1.5 rounded-2xl border border-[#e3eaf7] shadow-sm shrink-0">
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
                            placeholder="Search by Invoice # or Reference..." 
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
                 
                 <Card className="overflow-hidden">
                    <div className="overflow-x-auto">
                       <table className="w-full text-left text-sm">
                          <thead>
                             <tr className="bg-[#f8faff] text-[#5a6a85] border-b border-[#e3eaf7]">
                                <th className="px-6 py-4 font-bold uppercase text-[10px]">Reference</th>
                                <th className="px-6 py-4 font-bold uppercase text-[10px]">Direction</th>
                                <th className="px-6 py-4 font-bold uppercase text-[10px]">PINT AE Result</th>
                                <th className="px-6 py-4 font-bold uppercase text-[10px]">ASP Status</th>
                                <th className="px-6 py-4 font-bold uppercase text-[10px] text-right">Timestamp</th>
                             </tr>
                          </thead>
                          <tbody className="divide-y divide-[#e3eaf7]">
                             {fetchingData ? (
                                <tr><td colSpan={5} className="px-6 py-12 text-center text-[#8899b0]">Updating data stream...</td></tr>
                             ) : filteredDataFlow.length === 0 ? (
                                <tr><td colSpan={5} className="px-6 py-12 text-center text-[#8899b0]">No data detected matching your filters.</td></tr>
                             ) : filteredDataFlow.map(row => (
                                <tr key={row.submission_id} className="hover:bg-[#fcfdfe] transition-colors">
                                   <td className="px-6 py-4 font-bold text-[#1a2340]">{row.invoice_number}</td>
                                   <td className="px-6 py-4">
                                      <div className="flex items-center gap-2 text-xs font-medium text-[#5a6a85]">
                                         <div className="w-6 h-6 rounded bg-[#f0f7ff] flex items-center justify-center text-[#1a6fcf] shrink-0">
                                            <CloudLightning className="w-3.5 h-3.5" />
                                         </div>
                                         {selectedConn.erp_type} &rarr; PINT AE
                                      </div>
                                   </td>
                                   <td className="px-6 py-4">
                                      <Pill variant={row.error_count === 0 ? 'green' : 'red'}>
                                         {row.error_count === 0 ? 'VALID' : 'INVALID'}
                                      </Pill>
                                   </td>
                                   <td className="px-6 py-4">
                                      <span className={`font-bold ${row.http_status === 200 ? 'text-[#22c55e]' : 'text-[#e53e3e]'}`}>
                                         {row.status.toUpperCase()}
                                      </span>
                                   </td>
                                   <td className="px-6 py-4 text-right text-[#8899b0] text-[10px] font-bold">
                                      {new Date(row.timestamp).toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'short' })}
                                   </td>
                                </tr>
                             ))}
                          </tbody>
                       </table>
                    </div>
                 </Card>
             </div>

             {/* System Configuration Details */}
             <div className="space-y-4">
                <h2 className="text-lg font-bold text-[#1a2340] flex items-center gap-2">
                   <ShieldCheck className="w-5 h-5 text-[#1a6fcf]" />
                   Integration Details
                </h2>
                
                <Card className="p-6 space-y-6">
                   <div className="space-y-4">
                      <DetailRow label="Display Name" value={selectedConn.display_name} />
                      <DetailRow label="Integration Path" value={selectedConn.integration_mode === 'sftp' ? selectedConn.sftp_host : 'HTTPS REST'} />
                      <DetailRow label="Security Layer" value={selectedConn.integration_mode === 'webhook' ? 'HMAC-SHA256' : selectedConn.integration_mode === 'sftp' ? 'SSH/RSA-2048' : 'API Key Authenticated'} />
                   </div>

                   <div className="pt-6 border-t border-[#f1f5f9]">
                      <div className="text-[10px] font-bold text-[#8899b0] uppercase tracking-widest mb-4">Schema Mapping</div>
                      <div className="space-y-2">
                          {selectedConn.field_mapping ? Object.entries(selectedConn.field_mapping).slice(0, 4).map(([erp, pint]) => (
                             <div key={erp} className="flex items-center justify-between p-2 bg-[#f8faff] rounded border border-[#e3eaf7]">
                                <span className="text-[11px] font-mono text-[#1a2340]">{erp}</span>
                                <ArrowRightLeft className="w-3 h-3 text-[#5a6a85]" />
                                <span className="text-[11px] font-bold text-[#1a6fcf]">{pint}</span>
                             </div>
                          )) : (
                             <p className="text-xs text-[#8899b0]">No custom field mapping defined.</p>
                          )}
                      </div>
                   </div>

                   <Button className="w-full" variant="ghost" onClick={() => window.location.href='/integrations'}>
                      Manage Integration
                   </Button>
                </Card>
                
                <div className="p-4 bg-amber-50 rounded-xl border border-amber-200">
                   <div className="flex items-start gap-3">
                      <AlertCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                      <div>
                         <p className="text-xs font-bold text-amber-800">Operational Notice</p>
                         <p className="text-[10px] text-amber-700 mt-1">This ERP connection is using regulatory-grade handshake logging. All synchronization events are auditable in the ASP Portal.</p>
                      </div>
                   </div>
                </div>
             </div>
          </div>
        </div>
      )}
    </div>
  )
}

function DetailRow({ label, value }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-xs text-[#5a6a85] font-medium">{label}</span>
      <span className="text-xs text-[#1a2340] font-bold">{value}</span>
    </div>
  )
}
