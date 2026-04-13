import { useState, useEffect } from 'react'
import Card from '../components/ui/Card'
import { API_BASE } from '../constants/api'
import TrendChart from '../components/charts/TrendChart'
import Pill from '../components/ui/Pill'
import { Link } from 'react-router-dom'
import { FileText, CheckCircle, XCircle, ShieldCheck, X, ChevronRight } from 'lucide-react'
import toast from 'react-hot-toast'
import { API_HEADERS } from '../constants/apiHelpers'
import DateRangeFilter from '../components/ui/DateRangeFilter'

const PERIODS = [
  { key: 'daily', label: 'Today' },
  { key: 'monthly', label: 'Month' },
  { key: 'quarterly', label: 'Quarter' },
  { key: 'yearly', label: 'Year' },
  { key: 'all', label: 'All Time' },
  { key: 'custom', label: 'Custom Range' },
]

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [period, setPeriod] = useState('all')
  const [rulesData, setRulesData] = useState(null)
  const [showRulesModal, setShowRulesModal] = useState(false)
  const [loadingRules, setLoadingRules] = useState(false)
  const [dateRange, setDateRange] = useState({ start: '', end: '' })
  const user = JSON.parse(localStorage.getItem('uae_invoice_user') || '{}')

  useEffect(() => {
    loadSummary()
  }, [period, dateRange])

  async function loadSummary() {
    try {
      const q = new URLSearchParams()
      q.append('period', period)
      if (period === 'custom' && dateRange.start && dateRange.end) {
        q.append('start_date', dateRange.start)
        q.append('end_date', dateRange.end)
      }
      const res = await fetch(`${API_BASE}/api/v1/analytics/summary?${q.toString()}`, {
        headers: API_HEADERS
      })
      const json = await res.json()
      setData(json)
    } catch (e) {
      console.error(e)
    }
  }

  async function openRulesModal() {
    setShowRulesModal(true)
    if (!rulesData) {
      try {
        setLoadingRules(true)
        const q = new URLSearchParams()
        q.append('period', period)
        if (period === 'custom' && dateRange.start && dateRange.end) {
          q.append('start_date', dateRange.start)
          q.append('end_date', dateRange.end)
        }
        const res = await fetch(`${API_BASE}/api/v1/analytics/rules?${q.toString()}`, {
          headers: API_HEADERS
        })
        const json = await res.json()
        setRulesData(json)
      } catch (e) {
        toast.error('Failed to load rules data')
      } finally {
        setLoadingRules(false)
      }
    }
  }

  const rulesByCategory = rulesData?.rules?.reduce((acc, r) => {
    const cat = r.category || 'OTHER'
    if (!acc[cat]) acc[cat] = []
    acc[cat].push(r)
    return acc
  }, {}) || {}

  return (
    <div className="space-y-6">
      {/* Header with period toggle */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-[#1a2340]">
            Welcome back, {user.full_name?.split(' ')[0] || 'Admin'}
          </h1>
          <p className="text-sm text-[#5a6a85] mt-1">
            UAE PINT AE E-Invoice Engine · {new Date().toLocaleDateString('en-AE', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
          </p>
        </div>
        {/* Period Selector */}
        <div className="flex flex-col items-end gap-2">
          <div className="flex items-center gap-1 bg-[#f0f4ff] rounded-xl p-1">
            {PERIODS.map(p => (
              <button
                key={p.key}
                onClick={() => { setPeriod(p.key); setRulesData(null) }}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                  period === p.key
                    ? 'bg-white text-[#1a6fcf] shadow-sm'
                    : 'text-[#5a6a85] hover:text-[#1a2340]'
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
          {period === 'custom' && (
            <DateRangeFilter 
              onChange={(range) => { setDateRange(range); setRulesData(null); }}
              initialStart={dateRange.start}
              initialEnd={dateRange.end}
            />
          )}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-5 relative overflow-hidden group cursor-pointer hover:shadow-md transition-shadow">
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
            <FileText className="w-16 h-16 text-[#1a6fcf]" />
          </div>
          <div className="text-xs font-semibold text-[#8899b0] uppercase tracking-wider mb-2">Total Invoices</div>
          <div className="text-3xl font-bold text-[#1a2340]">{data?.total || 0}</div>
          <div className="text-xs text-[#22c55e] font-medium mt-2">↑ Active processing</div>
        </Card>

        <Card className="p-5 relative overflow-hidden group cursor-pointer hover:shadow-md transition-shadow">
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
            <CheckCircle className="w-16 h-16 text-[#22c55e]" />
          </div>
          <div className="text-xs font-semibold text-[#8899b0] uppercase tracking-wider mb-2">Pass Rate</div>
          <div className="text-3xl font-bold text-[#1a2340]">{data?.pass_rate || 0}%</div>
          <div className="text-xs text-[#5a6a85] font-medium mt-2">
            {PERIODS.find(p => p.key === period)?.label || 'All Time'}
          </div>
        </Card>

        <Card className="p-5 relative overflow-hidden group cursor-pointer hover:shadow-md transition-shadow">
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
            <XCircle className="w-16 h-16 text-[#e53e3e]" />
          </div>
          <div className="text-xs font-semibold text-[#8899b0] uppercase tracking-wider mb-2">Failures</div>
          <div className="text-3xl font-bold text-[#e53e3e]">{data?.failures || 0}</div>
          <div className="text-xs text-[#e53e3e] font-medium mt-2">Requires attention</div>
        </Card>

        {/* CLICKABLE RULES CARD */}
        <Card
          className="p-5 relative overflow-hidden group cursor-pointer hover:shadow-md hover:border-[#e07b00]/50 transition-all border border-transparent"
          onClick={openRulesModal}
        >
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
            <ShieldCheck className="w-16 h-16 text-[#e07b00]" />
          </div>
          <div className="text-xs font-semibold text-[#8899b0] uppercase tracking-wider mb-2">Rule Checks</div>
          <div className="text-3xl font-bold text-[#1a2340]">{rulesData?.total_rules || 51}</div>
          <div className="text-xs text-[#e07b00] font-medium mt-2 flex items-center gap-1">
            PINT AE fields covered <ChevronRight className="w-3 h-3" />
          </div>
        </Card>
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-6">
        <Card className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-lg font-semibold text-[#1a2340]">Validation trend (7 days)</h2>
            <Pill variant="blue">Live</Pill>
          </div>
          {data?.trend ? <TrendChart data={data.trend} /> : <div className="h-[200px] flex items-center justify-center text-[#8899b0]">No data</div>}
        </Card>

        <Card className="p-6 bg-gradient-to-br from-white to-[#f8faff] border-[#e3eaf7]">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-lg font-semibold text-[#1a2340]">Compliance timeline</h2>
            <Pill variant="green">On Track</Pill>
          </div>
          <div className="space-y-6">
            {[
              { label: 'ASP pre-approval', sub: 'Ministry of Finance', status: 'green', badge: 'COMPLETED' },
              { label: 'Legislative updates', sub: 'E-invoicing law published', status: 'green', badge: 'COMPLETED' },
              { label: 'Phase 1 go-live', sub: 'Integration period active', status: 'blue', badge: 'JUL 2026' },
              { label: 'Full mandate', sub: 'All UAE businesses', status: 'warning', badge: 'JUL 2027+' },
            ].map((item, i) => (
              <div key={i} className={`relative pl-6 ${i < 3 ? 'border-l-2' : ''} ${
                item.status === 'green' ? 'border-[#22c55e]' : item.status === 'blue' ? 'border-[#1a6fcf] border-dashed' : ''
              }`}>
                <div className={`absolute w-4 h-4 rounded-full -left-[9px] top-1 border-2 border-white flex items-center justify-center ${
                  item.status === 'green' ? 'bg-[#22c55e]' : item.status === 'blue' ? 'bg-[#1a6fcf] animate-pulse' : 'bg-[#e07b00]'
                }`}>
                  {item.status === 'green' && <CheckCircle className="w-3 h-3 text-white" />}
                </div>
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-sm font-semibold text-[#1a2340]">{item.label}</h3>
                    <p className="text-xs text-[#5a6a85] mt-0.5">{item.sub}</p>
                  </div>
                  <Pill variant={item.status === 'green' ? 'green' : item.status === 'blue' ? 'blue' : 'warning'}>{item.badge}</Pill>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Recent Runs */}
      <Card className="p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-lg font-semibold text-[#1a2340]">Recent runs</h2>
          <Link to="/history" className="text-sm text-[#1a6fcf] hover:underline font-medium">View all history</Link>
        </div>
        {data?.latest_runs && data.latest_runs.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="bg-[#f8faff] text-[#5a6a85]">
                <tr>
                  <th className="px-4 py-2 font-medium">Invoice #</th>
                  <th className="px-4 py-2 font-medium">Status</th>
                  <th className="px-4 py-2 font-medium">Compliance</th>
                  <th className="px-4 py-2 font-medium">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#e3eaf7]">
                {data.latest_runs.map((r) => (
                  <tr key={r.id} className="hover:bg-[#f8faff]">
                    <td className="px-4 py-3 font-medium text-[#1a2340]">{r.invoice_number}</td>
                    <td className="px-4 py-3">
                      <Pill variant={r.is_valid ? 'green' : 'red'}>{r.is_valid ? 'PASSED' : 'FAILED'}</Pill>
                    </td>
                    <td className="px-4 py-3 text-[#5a6a85]">{r.pass_percentage || 0}%</td>
                    <td className="px-4 py-3 text-[#8899b0] text-xs">{new Date(r.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center text-[#5a6a85] py-8 border-2 border-dashed border-[#e3eaf7] rounded-lg">
            Connect your system or run a manual validation to see real-time data here.
          </div>
        )}
      </Card>

      {/* RULES MODAL */}
      {showRulesModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#0a0f1e]/60 backdrop-blur-sm">
          <Card className="w-full max-w-5xl max-h-[85vh] flex flex-col shadow-2xl">
            <div className="p-5 border-b border-[#e3eaf7] flex items-center justify-between bg-[#f8faff] rounded-t-xl">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-[#e07b00]/10 rounded-lg">
                  <ShieldCheck className="w-5 h-5 text-[#e07b00]" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-[#1a2340]">
                    UAE PINT AE — All {rulesData?.total_rules || '51'} Validation Rules
                  </h3>
                  <p className="text-xs text-[#5a6a85]">
                    {rulesData?.total_invoices_checked || 0} invoices checked · Period: {PERIODS.find(p => p.key === period)?.label}
                  </p>
                </div>
              </div>
              <button onClick={() => setShowRulesModal(false)} className="p-1.5 hover:bg-[#e3eaf7] rounded-lg">
                <X className="w-5 h-5 text-[#8899b0]" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-5">
              {loadingRules ? (
                <div className="py-16 text-center text-[#5a6a85]">Loading live rule statistics...</div>
              ) : rulesData?.rules ? (
                <div className="space-y-6">
                  {Object.entries(rulesByCategory).map(([cat, rules]) => (
                    <div key={cat}>
                      <div className="flex items-center gap-2 mb-3">
                        <div className={`px-2 py-0.5 rounded text-xs font-bold uppercase tracking-wider text-white ${
                          cat === 'COMPLIANCE' ? 'bg-[#1a6fcf]' : cat === 'CALCULATION' ? 'bg-[#e07b00]' : 'bg-[#8899b0]'
                        }`}>{cat}</div>
                        <span className="text-xs text-[#8899b0]">{rules.length} rules</span>
                      </div>
                      <div className="space-y-2">
                        {rules.map((rule, i) => (
                          <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-[#f8faff] border border-[#e3eaf7] hover:border-[#1a6fcf]/30 transition-colors">
                            <div className={`w-2 h-2 rounded-full flex-shrink-0 ${rule.failed > 0 ? 'bg-[#e53e3e]' : 'bg-[#22c55e]'}`} />
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 flex-wrap">
                                <code className="text-[11px] font-mono bg-white border border-[#e3eaf7] px-1.5 py-0.5 rounded text-[#1a6fcf]">
                                  {rule.field}
                                </code>
                                <span className="text-sm text-[#1a2340] truncate">{rule.message}</span>
                              </div>
                            </div>
                            <div className="flex items-center gap-4 text-xs flex-shrink-0">
                              <div className="text-center">
                                <div className="font-bold text-[#22c55e]">{rule.passed}</div>
                                <div className="text-[#8899b0]">Pass</div>
                              </div>
                              <div className="text-center">
                                <div className="font-bold text-[#e53e3e]">{rule.failed}</div>
                                <div className="text-[#8899b0]">Fail</div>
                              </div>
                              <div className={`text-center min-w-[40px] font-bold ${rule.pass_rate >= 80 ? 'text-[#22c55e]' : rule.pass_rate >= 50 ? 'text-[#e07b00]' : 'text-[#e53e3e]'}`}>
                                {rule.pass_rate}%
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-16 text-center text-[#5a6a85]">No rules data available. Run some validations first.</div>
              )}
            </div>

            <div className="p-4 border-t border-[#e3eaf7] bg-[#f8faff] rounded-b-xl flex justify-between items-center">
              <span className="text-xs text-[#8899b0]">
                ✅ = PINT AE compliant · ❌ = requires remediation
              </span>
              <button
                onClick={() => setShowRulesModal(false)}
                className="px-4 py-2 bg-[#1a6fcf] text-white rounded-lg text-sm font-semibold hover:bg-[#1560b8] transition-colors"
              >
                Close
              </button>
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}
