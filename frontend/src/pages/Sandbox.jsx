import React, { useState, useEffect, useRef } from 'react'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Pill from '../components/ui/Pill'
import ProgressBar from '../components/ui/ProgressBar'
import { 
  Upload, Play, FileText, CheckCircle2, XCircle, Loader2, Info, 
  Settings as SettingsIcon, ShieldCheck, Database, RefreshCw, AlertCircle, Search
} from 'lucide-react'
import axios from 'axios'
import toast from 'react-hot-toast'
import { useAuth } from '../context/AuthContext'
import { getApiHeaders } from '../constants/apiHelpers'

const API_BASE = '/api/v1/sandbox'

export default function Sandbox() {
  const { token } = useAuth()
  const [file, setFile] = useState(null)
  const [isDragActive, setIsDragActive] = useState(false)
  const [running, setRunning] = useState(false)
  const [currentRun, setCurrentRun] = useState(null)
  const [includePint, setIncludePint] = useState(true)
  const [includeBusiness, setIncludeBusiness] = useState(true)
  const [includeFormat, setIncludeFormat] = useState(true)
  const fileInputRef = useRef(null)
  const client_id = "demo-client-phase2"

  useEffect(() => {
    let interval;
    if (currentRun && currentRun.status === 'RUNNING') {
      interval = setInterval(fetchRunStatus, 2000)
    }
    return () => clearInterval(interval)
  }, [currentRun])

  const fetchRunStatus = async () => {
    if (!currentRun?.run_id) return
    try {
      const res = await axios.get(`${API_BASE}/run-status/${currentRun.run_id}`, {
        headers: getApiHeaders(token)
      })
      setCurrentRun(prev => ({ ...prev, ...res.data }))
      if (res.data.status === 'COMPLETED') {
        setRunning(false)
        toast.success("Sandbox execution completed!")
      }
    } catch (err) {
      console.error("Status check failed")
    }
  }

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
    }
  }

  const startValidation = async () => {
    if (!file) {
      toast.error("Please select a file to validate")
      return
    }
    setRunning(true)
    const t = toast.loading("Initializing rule engine...")
    try {
      const formData = new FormData()
      formData.append('file', file)
      
      const params = new URLSearchParams()
      params.append('pint_rules', includePint)
      params.append('business_rules', includeBusiness)
      params.append('data_format', includeFormat)
      params.append('client_id', client_id)

      const res = await axios.post(`${API_BASE}/bulk-validate?${params.toString()}`, formData, {
        headers: {
          ...getApiHeaders(token),
          'Content-Type': 'multipart/form-data'
        }
      })
      setCurrentRun({ run_id: res.data.run_id, status: 'RUNNING' })
      toast.success("Extraction & Validation started", { id: t })
    } catch (err) {
      toast.error("Execution failed to start", { id: t })
      setRunning(false)
    }
  }

  return (
    <div className="p-8 max-w-[1400px] mx-auto animate-in fade-in duration-500 space-y-8">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="bg-[#1a2340] p-3 rounded-2xl shadow-lg">
            <ShieldCheck className="w-6 h-6 text-emerald-400" />
          </div>
          <div>
            <h1 className="text-3xl font-black text-[#1a2340] tracking-tight">PINT AE Sandbox</h1>
            <p className="text-[#5a6a85] font-medium">Compliance & Regulatory Validation Studio (568 test cases)</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Step 1: Upload */}
        <Card className="p-6 space-y-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-[#1a6fcf] font-bold text-xs uppercase tracking-widest">
              <span className="w-6 h-6 rounded-full bg-[#1a6fcf] text-white flex items-center justify-center text-[10px]">1</span>
              Data Ingestion
            </div>
            <Button 
              variant="ghost" 
              size="sm" 
              className="text-[10px] font-black h-7"
              onClick={async () => {
                 const res = await axios.get(`${API_BASE}/download-template`, {
                   responseType: 'blob',
                   headers: getApiHeaders(token)
                 })
                 const url = window.URL.createObjectURL(new Blob([res.data]))
                 const link = document.createElement('a')
                 link.href = url
                 link.setAttribute('download', 'PINT_AE_Sandbox_Template.csv')
                 document.body.appendChild(link)
                 link.click()
                 document.body.removeChild(link)
              }}
            >
              <FileText className="w-3 h-3 mr-1" /> Template
            </Button>
          </div>
          
          <div 
             className={`border-2 border-dashed rounded-2xl p-8 text-center transition-all cursor-pointer ${
               file ? 'border-emerald-500 bg-emerald-50' : 'border-[#e3eaf7] hover:border-[#1a6fcf] hover:bg-slate-50'
             }`}
             onClick={() => fileInputRef.current?.click()}
          >
             <input type="file" ref={fileInputRef} onChange={handleFileChange} className="hidden" />
             <Upload className={`w-8 h-8 mx-auto mb-4 ${file ? 'text-emerald-500' : 'text-[#8899b0]'}`} />
             {file ? (
               <div className="text-sm font-bold text-[#1a2340] truncate">{file.name}</div>
             ) : (
               <div className="text-xs font-medium text-[#8899b0]">Drop CSV/XLSX or click to browse</div>
             )}
          </div>
        </Card>

        {/* Step 2: Configuration */}
        <Card className="p-6 space-y-4">
          <div className="flex items-center gap-2 text-[#1a6fcf] font-bold text-xs uppercase tracking-widest">
            <span className="w-6 h-6 rounded-full bg-[#1a6fcf] text-white flex items-center justify-center text-[10px]">2</span>
            Rule Selection
          </div>
          
          <div className="space-y-2">
              <div 
                onClick={() => setIncludePint(!includePint)}
                className={`p-3 rounded-xl border-2 flex items-center justify-between cursor-pointer transition-all ${
                  includePint ? 'border-emerald-500 bg-emerald-50' : 'border-[#e3eaf7] bg-white'
                }`}
              >
                <span className={`text-xs font-bold ${includePint ? 'text-emerald-700' : 'text-[#5a6a85]'}`}>PINT Rules (Mandatory 51)</span>
                <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${includePint ? 'border-emerald-500 bg-emerald-500' : 'border-slate-300'}`}>
                  {includePint && <CheckCircle2 className="w-2.5 h-2.5 text-white" />}
                </div>
              </div>

              <div 
                onClick={() => setIncludeBusiness(!includeBusiness)}
                className={`p-3 rounded-xl border-2 flex items-center justify-between cursor-pointer transition-all ${
                  includeBusiness ? 'border-blue-500 bg-blue-50' : 'border-[#e3eaf7] bg-white'
                }`}
              >
                <span className={`text-xs font-bold ${includeBusiness ? 'text-blue-700' : 'text-[#5a6a85]'}`}>Business Logic & Tax</span>
                <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${includeBusiness ? 'border-blue-500 bg-blue-500' : 'border-slate-300'}`}>
                  {includeBusiness && <CheckCircle2 className="w-2.5 h-2.5 text-white" />}
                </div>
              </div>

              <div 
                onClick={() => setIncludeFormat(!includeFormat)}
                className={`p-3 rounded-xl border-2 flex items-center justify-between cursor-pointer transition-all ${
                  includeFormat ? 'border-amber-500 bg-amber-50' : 'border-[#e3eaf7] bg-white'
                }`}
              >
                <span className={`text-xs font-bold ${includeFormat ? 'text-amber-700' : 'text-[#5a6a85]'}`}>Data Format & Schema</span>
                <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${includeFormat ? 'border-amber-500 bg-amber-500' : 'border-slate-300'}`}>
                  {includeFormat && <CheckCircle2 className="w-2.5 h-2.5 text-white" />}
                </div>
              </div>
          </div>
        </Card>

        {/* Step 3: Run */}
        <Card className="p-6 flex flex-col justify-between">
          <div className="flex items-center gap-2 text-[#1a6fcf] font-bold text-xs uppercase tracking-widest">
            <span className="w-6 h-6 rounded-full bg-[#1a6fcf] text-white flex items-center justify-center text-[10px]">3</span>
            Execute
          </div>
          
          <div className="py-4">
             <div className="bg-[#f8faff] p-4 rounded-xl border border-[#e3eaf7] mb-6">
                <div className="text-[10px] font-black text-[#5a6a85] uppercase mb-1">Target Engine</div>
                <div className="text-sm font-bold text-[#1a2340]">UAE_PINT_AE_QA_V2.1</div>
             </div>
             
             <Button 
                onClick={startValidation} 
                disabled={!file || running} 
                className="w-full h-14 rounded-2xl bg-[#1a2340] hover:bg-black text-white font-bold shadow-xl shadow-[#1a2340]/20 flex items-center justify-center gap-2"
             >
                {running ? <Loader2 className="w-5 h-5 animate-spin" /> : <Play className="w-5 h-5" />}
                {running ? 'Processing...' : 'Run Sandbox Suite'}
             </Button>
          </div>
        </Card>
      </div>

      {/* Results Section */}
      {currentRun && (
        <Card className="rounded-[2rem] overflow-hidden border-[#e3eaf7] shadow-xl">
          <div className="bg-[#1a2340] p-8 text-white">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
              <div>
                <div className="text-[10px] font-black uppercase tracking-[0.2em] text-[#1a6fcf] mb-2">Execution Outcome</div>
                <h2 className="text-3xl font-black">{currentRun.status === 'COMPLETED' ? `Pass Rate: ${currentRun.pass_rate?.toFixed(1)}%` : 'Processing...'}</h2>
              </div>
              <div className="flex gap-8">
                <div className="text-center">
                  <div className="text-2xl font-black text-emerald-400">{currentRun.passed || 0}</div>
                  <div className="text-[10px] font-black uppercase text-slate-400">Passed</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-black text-rose-500">{currentRun.failed || 0}</div>
                  <div className="text-[10px] font-black uppercase text-slate-400">Failed</div>
                </div>
                <div className="text-center border-l border-white/10 pl-8">
                  <div className="text-2xl font-black">{currentRun.total || 0}</div>
                  <div className="text-[10px] font-black uppercase text-slate-400">Rules Run</div>
                </div>
              </div>
            </div>
          </div>

          {currentRun.summary && (
            <div className="p-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 bg-slate-50">
               {Object.entries(currentRun.summary).map(([name, stats]) => (
                 <div key={name} className="bg-white p-6 rounded-2xl border border-[#e3eaf7] shadow-sm space-y-4">
                    <div className="flex justify-between items-start">
                       <span className="text-[10px] font-black text-[#8899b0] uppercase leading-tight max-w-[150px]">{name}</span>
                       <Pill variant={stats.failed === 0 ? 'green' : 'amber'} className="text-[9px]">{Math.round((stats.passed / stats.total) * 100)}%</Pill>
                    </div>
                    <div className="flex items-end justify-between">
                       <div className="text-2xl font-black text-[#1a2340]">{stats.passed}<span className="text-sm text-[#8899b0] font-bold">/{stats.total}</span></div>
                    </div>
                    <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                       <div className="h-full bg-[#16a34a]" style={{ width: `${(stats.passed / stats.total) * 100}%` }} />
                    </div>
                 </div>
               ))}
            </div>
          )}

          {currentRun.results && (
             <div className="p-8 border-t border-[#e3eaf7]">
                <h3 className="text-lg font-bold text-[#1a2340] mb-4">Detailed Breakdown (Top 100)</h3>
                <div className="overflow-x-auto">
                   <table className="w-full text-left text-sm whitespace-nowrap">
                      <thead>
                         <tr className="text-[#8899b0] border-b border-[#e3eaf7]">
                            <th className="pb-4 font-black uppercase text-[10px]">Test Case</th>
                            <th className="pb-4 font-black uppercase text-[10px]">Expected Behavior</th>
                            <th className="pb-4 font-black uppercase text-[10px]">Outcome</th>
                            <th className="pb-4 font-black uppercase text-[10px]">Status</th>
                         </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                         {currentRun.results.map((r, i) => (
                           <tr key={i} className="hover:bg-slate-50 transition-colors">
                              <td className="py-4 font-bold text-[#1a2340]">{r.id}</td>
                              <td className="py-4 text-[#5a6a85] text-xs max-w-xs truncate">{r.expected}</td>
                              <td className="py-4 text-[#5a6a85] text-xs max-w-xs truncate">{r.actual}</td>
                              <td className="py-4">
                                 <Pill variant={r.status === 'PASS' ? 'green' : 'red'}>{r.status}</Pill>
                              </td>
                           </tr>
                         ))}
                      </tbody>
                   </table>
                </div>
             </div>
          )}
        </Card>
      )}

      {/* Empty State */}
      {!currentRun && !running && (
        <div className="flex flex-col items-center justify-center py-24 text-center space-y-4 opacity-40">
           <Database className="w-16 h-16 text-[#8899b0]" />
           <div>
              <h3 className="text-xl font-bold text-[#1a2340]">Suite Ready for Execution</h3>
              <p className="text-sm font-medium text-[#8899b0]">Upload a dataset and select rule sets to begin</p>
           </div>
        </div>
      )}
    </div>
  )
}
