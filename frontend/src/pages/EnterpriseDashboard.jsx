import React, { useState, useEffect } from 'react'
import { LayoutDashboard, Target, AlertTriangle, CheckCircle2, FileText, Activity, ShieldCheck, Zap } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, AreaChart, Area } from 'recharts'
import axios from 'axios'
import { useAuth } from '../context/AuthContext'
import { getApiHeaders } from '../constants/apiHelpers'

const API_BASE = '/api/v1/enterprise'

export default function EnterpriseDashboard() {
  const { token } = useAuth()
  const [executive, setExecutive] = useState(null)
  const [heatmap, setHeatmap] = useState([])
  const [testHistory, setTestHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const client_id = "demo-client-phase2" // Aligned with TestRunner ID

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      const config = { headers: getApiHeaders(token) }
      const [execRes, heatRes, testRes] = await Promise.all([
        axios.get(`${API_BASE}/executive?client_id=${client_id}`, config),
        axios.get(`${API_BASE}/heatmap?client_id=${client_id}`, config),
        axios.get(`${API_BASE}/test-history?client_id=${client_id}`, config)
      ])
      setExecutive(execRes.data.summary)
      setHeatmap(heatRes.data)
      setTestHistory(testRes.data)
    } catch (err) {
      console.error("Error fetching enterprise data", err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="p-8 text-[#5a6a85]">Loading Command Center...</div>

  return (
    <div className="p-8 max-w-[1400px] mx-auto animate-in fade-in duration-500">
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-3">
          <div className="bg-[#1a6fcf] p-2 rounded-lg">
            <Zap className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-[#1a2b4b]">Executive Analytics</h1>
            <p className="text-sm text-[#5a6a85] font-medium">UAE PINT AE Compliance Monitoring</p>
          </div>
        </div>
        <div className="flex items-center gap-3 bg-white p-2 rounded-xl border border-[#e3eaf7] shadow-sm">
          <div className="w-10 h-10 rounded-lg bg-[#f0f7ff] flex items-center justify-center text-[#1a6fcf]">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <div className="text-[10px] text-[#8899b0] uppercase font-bold">Client Tier</div>
            <div className="text-sm font-bold text-[#1a2340]">Premium Enterprise</div>
          </div>
        </div>
      </div>

      {/* SECTION 1: Executive Tiles */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <Tile 
          label="Total Submissions" 
          value={executive?.total_invoices} 
          icon={FileText} 
          color="blue" 
          trend="+12%"
        />
        <Tile 
          label="Acceptance Rate" 
          value={`${executive?.acceptance_rate ?? 0}%`} 
          icon={Target} 
          color="green" 
          subText={`Benchmark: ${executive?.target_benchmark ?? 98}%`}
          isAlert={executive?.acceptance_rate ? executive.acceptance_rate < (executive.target_benchmark ?? 98) : false}
        />
        <Tile 
          label="Rejection Rate" 
          value={`${(100 - (executive?.acceptance_rate ?? 100)).toFixed(1)}%`} 
          icon={AlertTriangle} 
          color="red" 
        />
        <Tile 
          label="System Health" 
          value="99.9%" 
          icon={Activity} 
          color="indigo" 
          trend="Stable"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* SECTION 2: Compliance Heatmap */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-[#e3eaf7] p-6 shadow-sm">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-bold text-[#1a2340]">51-Field Compliance Heatmap</h2>
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1.5 text-[10px] font-bold text-[#8899b0] uppercase">
                <div className="w-2 h-2 rounded-full bg-[#22c55e]" /> High Pass
              </span>
              <span className="flex items-center gap-1.5 text-[10px] font-bold text-[#8899b0] uppercase">
                <div className="w-2 h-2 rounded-full bg-[#faad14]" /> Warning
              </span>
              <span className="flex items-center gap-1.5 text-[10px] font-bold text-[#8899b0] uppercase">
                <div className="w-2 h-2 rounded-full bg-[#ef4444]" /> Critical
              </span>
            </div>
          </div>
          
          <div className="grid grid-cols-6 sm:grid-cols-8 md:grid-cols-10 gap-3">
            {heatmap.map((m, idx) => (
              <HeatMapCell key={idx} data={m} />
            ))}
            {/* Filler for empty spots to show total scale */}
            {Array.from({ length: Math.max(0, 51 - heatmap.length) }).map((_, i) => (
              <div key={`empty-${i}`} className="aspect-square bg-[#f8faff] border border-dashed border-[#e3eaf7] rounded-lg" />
            ))}
          </div>
          <div className="mt-6 pt-6 border-t border-[#f1f5f9] text-[#8899b0] text-[11px] italic">
            * Every block represents a PINT AE mandatory field. Red/Orange indicates systematic rejection clusters.
          </div>
        </div>

        {/* SECTION 3: Test Pass Trend */}
        <div className="bg-white rounded-2xl border border-[#e3eaf7] p-6 shadow-sm">
          <h2 className="text-lg font-bold text-[#1a2340] mb-6">QA Pass Rate Trend</h2>
          <div className="h-[280px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={testHistory.reverse()}>
                <defs>
                  <linearGradient id="colorPass" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#1a6fcf" stopOpacity={0.1}/>
                    <stop offset="95%" stopColor="#1a6fcf" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="run_id" hide />
                <Tooltip 
                  contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                  formatter={(val) => [`${val}%`, 'Pass Rate']}
                />
                <Area type="monotone" dataKey="pass_rate" stroke="#1a6fcf" strokeWidth={3} fillOpacity={1} fill="url(#colorPass)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-8">
            <h3 className="text-sm font-bold text-[#1a2340] mb-4">Recent Test Batches</h3>
            <div className="space-y-3">
              {testHistory.slice(0, 4).map(run => (
                <div key={run.run_id} className="flex items-center justify-between p-3 bg-[#f8faff] rounded-xl border border-[#e3eaf7]">
                   <div className="flex items-center gap-3">
                      <Zap className={`w-4 h-4 ${run.pass_rate === 100 ? 'text-[#22c55e]' : 'text-[#1a6fcf]'}`} />
                      <div>
                        <div className="text-[11px] font-bold text-[#1a2340]">{run.run_id.slice(0, 8)}</div>
                        <div className="text-[10px] text-[#8899b0] uppercase">{run.run_type}</div>
                      </div>
                   </div>
                   <div className="text-right">
                      <div className={`text-sm font-bold ${run.pass_rate > 90 ? 'text-[#22c55e]' : 'text-[#1a2340]'}`}>{run.pass_rate.toFixed(1)}%</div>
                      <div className="text-[10px] text-[#8899b0] uppercase">{run.passed} / {run.failed + run.passed}</div>
                   </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function Tile({ label, value, icon: Icon, color, trend, subText, isAlert }) {
  const colors = {
    blue: 'bg-[#f0f7ff] text-[#1a6fcf]',
    green: 'bg-[#f0fff4] text-[#22c55e]',
    red: 'bg-[#fff5f5] text-[#e53e3e]',
    indigo: 'bg-[#f5f3ff] text-[#6366f1]'
  }
  return (
    <div className={`bg-white p-6 rounded-2xl border ${isAlert ? 'border-red-200' : 'border-[#e3eaf7]'} shadow-sm relative overflow-hidden`}>
      <div className={`w-12 h-12 rounded-xl ${colors[color]} flex items-center justify-center mb-4`}>
        <Icon className="w-6 h-6" />
      </div>
      <div className="text-xs font-bold text-[#8899b0] uppercase tracking-wider">{label}</div>
      <div className="text-3xl font-black text-[#1a2340] mt-1">{value}</div>
      {trend && <div className="text-[10px] font-bold text-[#22c55e] mt-2">{trend} vs last month</div>}
      {subText && <div className={`text-[10px] font-bold mt-2 ${isAlert ? 'text-[#e53e3e]' : 'text-[#8899b0]'}`}>{subText}</div>}
    </div>
  )
}

function HeatMapCell({ data }) {
  const rate = data.compliance_rate
  const bgColor = rate > 95 ? 'bg-[#22c55e]' : rate > 80 ? 'bg-[#faad14]' : 'bg-[#ef4444]'
  
  return (
    <div className="group relative">
      <div className={`aspect-square rounded-lg shadow-sm transition-transform hover:scale-110 cursor-help ${bgColor}`} />
      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-32 hidden group-hover:block bg-[#1a2340] text-white p-2 rounded-lg text-[10px] z-50 shadow-xl">
        <div className="font-bold border-b border-white/20 mb-1 pb-1">{data.field}</div>
        <div>Rate: <span className="font-bold">{rate}%</span></div>
        <div>Checks: {data.total_checks}</div>
      </div>
    </div>
  )
}
