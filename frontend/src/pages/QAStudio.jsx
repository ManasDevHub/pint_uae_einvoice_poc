import React, { useState, useEffect } from 'react'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Pill from '../components/ui/Pill'
import { Upload, Play, Zap, FileText, CheckCircle2, XCircle, Loader2, Info, Cpu } from 'lucide-react'
import axios from 'axios'
import toast from 'react-hot-toast'
import { useAuth } from '../context/AuthContext'
import { getApiHeaders } from '../constants/apiHelpers'

const API_BASE = '/api/v1/qa'

export default function QAStudio() {
  const { token } = useAuth()
  const [file, setFile] = useState(null)
  const [runs, setRuns] = useState([])
  const [loading, setLoading] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [includePint, setIncludePint] = useState(true)
  const [includeBusiness, setIncludeBusiness] = useState(true)
  const client_id = "demo-client-phase2"

  useEffect(() => {
    fetchRuns()
    const interval = setInterval(fetchRuns, 5000)
    return () => clearInterval(interval)
  }, [])

  const fetchRuns = async () => {
    try {
      setRefreshing(true)
      const res = await axios.get(`${API_BASE}/status?client_id=${client_id}`, {
        headers: getApiHeaders(token)
      })
      setRuns(res.data)
    } catch (err) {
      console.error("Failed to fetch QA status")
    } finally {
      setRefreshing(false)
    }
  }

  const triggerRun = async (type = 'full', limit = 558) => {
    try {
      setLoading(true)
      const params = `client_id=${client_id}&run_type=${type}&limit=${limit}&include_pint=${includePint}&include_business=${includeBusiness}`
      await axios.post(`${API_BASE}/trigger-run?${params}`, {}, {
        headers: getApiHeaders(token)
      })
      toast.success(`Sandbox execution engine started: ${includePint ? 'PINT' : ''} ${includeBusiness ? 'Business' : ''}`)
      fetchRuns()
    } catch (err) {
      toast.error(err.response?.data?.detail || "Execution failed to start")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-8 max-w-[1240px] mx-auto animate-in fade-in duration-500">
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-3">
          <div className="bg-[#1a2340] p-2 rounded-lg">
            <Cpu className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-[#1a2340]">PINT AE Sandbox</h1>
            <p className="text-[#5a6a85] text-sm mt-1">Enterprise regression testing (558 extracted UAE PINT AE test cases)</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
        {/* Rule Selection Parameters */}
        <Card className="p-6">
          <h2 className="text-lg font-bold text-[#1a2340] mb-4 flex items-center gap-2">
            <SettingsIcon className="w-5 h-5 text-[#1a6fcf]" /> Rule Set Configuration
          </h2>
          <p className="text-xs text-[#8899b0] mb-6">Select which rule sets to execute from the 558-case repository.</p>
          
          <div className="space-y-4">
            <div 
              onClick={() => setIncludePint(!includePint)}
              className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${includePint ? 'border-[#16a34a] bg-[#f0fdf4]' : 'border-[#e3eaf7] bg-white'}`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <ShieldCheck className={`w-5 h-5 ${includePint ? 'text-[#16a34a]' : 'text-[#8899b0]'}`} />
                  <div>
                    <div className="text-sm font-bold text-[#1a2340]">Mandatory PINT Compliance</div>
                    <div className="text-[10px] font-bold text-[#166534] uppercase">51 Core Rules</div>
                  </div>
                </div>
                <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${includePint ? 'border-[#16a34a] bg-[#16a34a]' : 'border-[#cbd5e1]'}`}>
                  {includePint && <CheckCircle2 className="w-3 h-3 text-white" />}
                </div>
              </div>
            </div>

            <div 
              onClick={() => setIncludeBusiness(!includeBusiness)}
              className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${includeBusiness ? 'border-[#1a6fcf] bg-[#f0f7ff]' : 'border-[#e3eaf7] bg-white'}`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Database className={`w-5 h-5 ${includeBusiness ? 'text-[#1a6fcf]' : 'text-[#8899b0]'}`} />
                  <div>
                    <div className="text-sm font-bold text-[#1a2340]">Enterprise Business Logic</div>
                    <div className="text-[10px] font-bold text-[#1a6fcf] uppercase">Extracted Calculation Rules</div>
                  </div>
                </div>
                <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${includeBusiness ? 'border-[#1a6fcf] bg-[#1a6fcf]' : 'border-[#cbd5e1]'}`}>
                  {includeBusiness && <CheckCircle2 className="w-3 h-3 text-white" />}
                </div>
              </div>
            </div>
          </div>
        </Card>

        {/* Execution Control */}
        <Card className="p-6">
          <h2 className="text-lg font-bold text-[#1a2340] mb-4 flex items-center gap-2">
            <Play className="w-5 h-5 text-[#22c55e]" /> Execution Control
          </h2>
          <div className="space-y-4">
             <div className="bg-[#fefce8] border border-[#fef08a] p-4 rounded-xl flex items-start gap-3">
                <Info className="w-5 h-5 text-[#854d0e] mt-0.5" />
                <div className="text-xs text-[#854d0e] leading-relaxed">
                  <strong>PINT Simulation Engine:</strong> Testing against 558 regression scenarios extracted from <code>QA_TestCases_v2.xlsx</code>.
                </div>
             </div>
             
             <div className="grid grid-cols-2 gap-4">
                <button 
                  onClick={() => triggerRun('quick', 25)}
                  disabled={loading || (!includePint && !includeBusiness)}
                  className="p-4 bg-white border border-[#e3eaf7] rounded-xl hover:shadow-md transition-all text-left"
                >
                  <div className="text-[10px] font-bold text-[#8899b0] uppercase mb-1">Fast Track</div>
                  <div className="text-sm font-bold text-[#1a2340]">Quick Validate</div>
                  <div className="text-[10px] text-[#22c55e] font-bold mt-2">Top 25 Criticals</div>
                </button>
                <button 
                  onClick={() => triggerRun('full', 558)}
                  disabled={loading || (!includePint && !includeBusiness)}
                  className="p-4 bg-[#1a2340] border border-[#1a2340] rounded-xl hover:shadow-lg transition-all text-left shadow-lg shadow-[#1a2340]/20"
                >
                  <div className="text-[10px] font-bold text-white/60 uppercase mb-1">Full Regression</div>
                  <div className="text-sm font-bold text-white">Execute All 558</div>
                  <div className="text-[10px] text-[#22c55e] font-bold mt-2">Complete Audit</div>
                </button>
             </div>
             
             {loading && (
               <div className="flex items-center gap-2 text-xs font-bold text-[#1a6fcf] animate-pulse justify-center py-2">
                 <Loader2 className="w-4 h-4 animate-spin" />
                 Initializing Multi-segment Engine...
               </div>
             )}
          </div>
        </Card>
      </div>

      {/* Test Run History */}
      <h3 className="text-sm font-bold text-[#8899b0] uppercase mb-4 tracking-widest flex items-center justify-between">
        Regression History & Breakdown
        {refreshing && <Loader2 className="w-3 h-3 animate-spin" />}
      </h3>
      <div className="space-y-4">
        {(!Array.isArray(runs) || runs.length === 0) ? (
          <div className="p-12 text-center text-[#8899b0] bg-white rounded-2xl border border-dashed border-[#e3eaf7]">
            No live test batches found. Start an execution above.
          </div>
        ) : runs.map(run => (
          <Card key={run.id} className="overflow-hidden border-[#e3eaf7] hover:border-[#1a6fcf] transition-colors">
             <div className="p-4 flex items-center justify-between bg-white">
                <div className="flex items-center gap-4">
                   <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${run.status === 'COMPLETED' ? 'bg-[#f0fdf4] text-[#22c55e]' : 'bg-[#fffbeb] text-[#d97706]'}`}>
                      {run.status === 'COMPLETED' ? <CheckCircle2 className="w-6 h-6" /> : <Loader2 className="w-6 h-6 animate-spin" />}
                   </div>
                   <div>
                      <div className="text-xs font-bold text-[#1a2340] mb-0.5">BATCH ID: {run.id?.slice(0, 8) || 'N/A'}</div>
                      <div className="text-[10px] text-[#8899b0] font-bold uppercase tracking-tighter">
                        {run.run_type} | {run.start_time ? new Date(run.start_time).toLocaleString() : 'N/A'}
                      </div>
                   </div>
                </div>
                <div className="text-right flex items-center gap-8">
                   <div>
                      <div className="text-[10px] text-[#8899b0] uppercase font-bold text-center mb-1">Accuracy</div>
                      <div className={`text-sm font-black ${run.pass_rate > 90 ? 'text-[#22c55e]' : 'text-[#1a2340]'}`}>{run.pass_rate?.toFixed(1) || '0.0'}%</div>
                   </div>
                   <Pill variant={run.status === 'COMPLETED' ? 'green' : 'amber'}>
                      {run.status || 'PENDING'}
                   </Pill>
                </div>
             </div>
             
             {run.segmented_summary && (
               <div className="px-4 py-3 bg-[#f8faff] border-t border-[#e3eaf7] grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                  {Object.entries(run.segmented_summary).map(([name, stats]) => (
                    <div key={name} className="space-y-1">
                      <div className="text-[9px] font-bold text-[#8899b0] uppercase truncate" title={name}>{name.replace('A1  ', '')}</div>
                      <div className="flex items-center justify-between">
                        <div className="text-[10px] font-black text-[#1a2340]">{stats.p}/{stats.p + stats.f}</div>
                        <div className="text-[9px] font-bold text-[#22c55e]">{Math.round((stats.p / (stats.p + stats.f || 1)) * 100)}%</div>
                      </div>
                      <div className="h-1 bg-[#e2e8f0] rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-[#22c55e]" 
                          style={{ width: `${(stats.p / (stats.p + stats.f || 1)) * 100}%` }}
                        />
                      </div>
                    </div>
                  ))}
               </div>
             )}
          </Card>
        ))}
      </div>
    </div>
  )
}
