import { useState, useEffect } from 'react'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import TrendChart from '../components/charts/TrendChart'
import DonutChart from '../components/charts/DonutChart'
import { API_BASE } from '../constants/api'
import { X, Download, AlertCircle, ExternalLink, CheckCircle2, Search } from 'lucide-react'
import toast from 'react-hot-toast'
import { downloadCsv, API_HEADERS } from '../constants/apiHelpers'

const PERIODS = [
  { key: 'all', label: 'All Time' },
  { key: 'daily', label: 'Today' },
  { key: 'monthly', label: 'Month' },
  { key: 'quarterly', label: 'Quarter' },
  { key: 'yearly', label: 'Year' },
]

export default function Analytics() {
  const [data, setData] = useState(null)
  const [rulesData, setRulesData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [loadingRules, setLoadingRules] = useState(false)
  const [period, setPeriod] = useState('all')
  const [selectedField, setSelectedField] = useState(null)
  const [failures, setFailures] = useState([])
  const [loadingFailures, setLoadingFailures] = useState(false)
  const [ruleSearch, setRuleSearch] = useState('')
  const [activeTab, setActiveTab] = useState('overview') // 'overview' | 'rules'

  useEffect(() => {
    loadSummary()
    loadRules()
  }, [period])

  async function loadSummary() {
    try {
      setLoading(true)
      const res = await fetch(`${API_BASE}/api/v1/analytics/summary?period=${period}`, {
        headers: API_HEADERS
      })
      const json = await res.json()
      setData(json)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  async function loadRules() {
    try {
      setLoadingRules(true)
      const res = await fetch(`${API_BASE}/api/v1/analytics/rules?period=${period}`, {
        headers: API_HEADERS
      })
      const json = await res.json()
      setRulesData(json)
    } catch (e) {
      console.error('Failed to load rules', e)
    } finally {
      setLoadingRules(false)
    }
  }

  const handleFieldClick = async (field) => {
    setSelectedField(field)
    try {
      setLoadingFailures(true)
      const res = await fetch(`${API_BASE}/api/v1/analytics/failures/${field}`, {
        headers: API_HEADERS
      })
      const json = await res.json()
      setFailures(json.items || [])
    } catch (e) {
      toast.error('Failed to load failure details')
    } finally {
      setLoadingFailures(false)
    }
  }

  const handleExportFailures = async () => {
    if (!selectedField) return
    try {
      await downloadCsv(
        `${API_BASE}/api/v1/analytics/failures/${selectedField}/export`,
        `failures_${selectedField}.csv`
      )
      toast.success('Failure report downloaded')
    } catch (e) {
      toast.error(`Export failed: ${e.message}`)
    }
  }

  const filteredRules = rulesData?.rules?.filter(r =>
    !ruleSearch ||
    r.field.toLowerCase().includes(ruleSearch.toLowerCase()) ||
    r.message.toLowerCase().includes(ruleSearch.toLowerCase()) ||
    r.category.toLowerCase().includes(ruleSearch.toLowerCase())
  ) || []

  if (loading) return <div className="p-8 text-[#5a6a85]">Loading analytics...</div>

  return (
    <div className="space-y-6">
      {/* Header with period toggle */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-[#1a2340]">Analytics</h1>
          <p className="text-sm text-[#5a6a85] mt-1">Validation performance and rule-level diagnostic data</p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <div className="flex items-center gap-1 bg-[#f0f4ff] rounded-xl p-1">
            {PERIODS.map(p => (
              <button
                key={p.key}
                onClick={() => setPeriod(p.key)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                  period === p.key ? 'bg-white text-[#1a6fcf] shadow-sm' : 'text-[#5a6a85] hover:text-[#1a2340]'
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
          <Button variant="ghost" onClick={() => { loadSummary(); loadRules() }} size="sm">Refresh</Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 border-b border-[#e3eaf7]">
        {[
          { key: 'overview', label: 'Overview' },
          { key: 'rules', label: `All Rules (${rulesData?.total_rules || 51})` },
        ].map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-3 text-sm font-semibold border-b-2 transition-colors ${
              activeTab === tab.key
                ? 'border-[#1a6fcf] text-[#1a6fcf]'
                : 'border-transparent text-[#5a6a85] hover:text-[#1a2340]'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'overview' && (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="p-6">
              <h2 className="text-sm font-semibold text-[#8899b0] uppercase tracking-wider mb-4">Pass Rate Trend (7 days)</h2>
              {data?.trend ? <TrendChart data={data.trend} /> : <div className="h-48 flex items-center justify-center text-[#8899b0]">No data yet</div>}
            </Card>
            <Card className="p-6">
              <h2 className="text-sm font-semibold text-[#8899b0] uppercase tracking-wider mb-4">Error Breakdown by Category</h2>
              {data?.by_category?.length > 0 ? <DonutChart data={data.by_category} /> : <div className="h-48 flex items-center justify-center text-[#8899b0]">No errors recorded</div>}
            </Card>
          </div>

          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-[#8899b0] uppercase tracking-wider">Top Failing Fields</h2>
              <span className="text-xs text-[#8899b0]">Click any row to drill down</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-[#f8faff] text-[#5a6a85]">
                  <tr>
                    <th className="px-4 py-3 font-medium">Field / Rule</th>
                    <th className="px-4 py-3 font-medium text-right">Failures</th>
                    <th className="px-4 py-3 font-medium text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {(data?.top_errors || []).map((err, i) => (
                    <tr
                      key={i}
                      onClick={() => handleFieldClick(err.field)}
                      className="group cursor-pointer hover:bg-[#f0f4ff] transition-colors"
                    >
                      <td className="px-4 py-4 font-medium text-[#1a2340] border-b border-[#e3eaf7] group-hover:text-[#1a6fcf]">
                        <div className="flex items-center gap-2">
                          <code className="text-xs bg-[#f0f4ff] px-2 py-0.5 rounded">{err.field}</code>
                          <ExternalLink className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                        </div>
                      </td>
                      <td className="px-4 py-4 text-right font-bold text-[#e53e3e] border-b border-[#e3eaf7]">{err.count}</td>
                      <td className="px-4 py-4 text-right border-b border-[#e3eaf7]">
                        <button className="text-xs text-[#1a6fcf] hover:underline">View Details</button>
                      </td>
                    </tr>
                  ))}
                  {(!data?.top_errors || data.top_errors.length === 0) && (
                    <tr>
                      <td colSpan={3} className="px-4 py-8 text-center text-[#5a6a85]">
                        <CheckCircle2 className="w-8 h-8 text-[#22c55e] mx-auto mb-2" />
                        No failures recorded for this period. All clear!
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </Card>
        </>
      )}

      {activeTab === 'rules' && (
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
            <div>
              <h2 className="text-sm font-semibold text-[#8899b0] uppercase tracking-wider">All PINT AE Validation Rules</h2>
              <p className="text-xs text-[#8899b0] mt-1">
                {rulesData?.total_invoices_checked || 0} invoices checked · {rulesData?.total_rules || 0} rules evaluated · Shows all positive + negative checks
              </p>
            </div>
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[#8899b0]" />
              <input
                type="text"
                placeholder="Search rules..."
                value={ruleSearch}
                onChange={e => setRuleSearch(e.target.value)}
                className="pl-9 pr-4 py-2 border border-[#e3eaf7] rounded-lg text-sm focus:outline-none focus:border-[#1a6fcf] w-64"
              />
            </div>
          </div>

          {loadingRules ? (
            <div className="py-16 text-center text-[#5a6a85]">Loading rule statistics...</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-[#f8faff] text-[#5a6a85] sticky top-0">
                  <tr>
                    <th className="px-4 py-3 font-medium">Field</th>
                    <th className="px-4 py-3 font-medium">Rule Description</th>
                    <th className="px-4 py-3 font-medium">Category</th>
                    <th className="px-4 py-3 font-medium text-center">✅ Passed</th>
                    <th className="px-4 py-3 font-medium text-center">❌ Failed</th>
                    <th className="px-4 py-3 font-medium text-center">Pass Rate</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#e3eaf7]">
                  {filteredRules.map((rule, i) => (
                    <tr
                      key={i}
                      className={`hover:bg-[#f8faff] cursor-pointer ${rule.failed > 0 ? '' : ''}`}
                      onClick={() => rule.failed > 0 && handleFieldClick(rule.field)}
                    >
                      <td className="px-4 py-3">
                        <code className="text-[11px] font-mono bg-[#f0f4ff] border border-[#e3eaf7] px-2 py-1 rounded text-[#1a6fcf]">
                          {rule.field}
                        </code>
                      </td>
                      <td className="px-4 py-3 text-[#1a2340] text-xs max-w-xs">{rule.message}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase text-white ${
                          rule.category === 'COMPLIANCE' ? 'bg-[#1a6fcf]' :
                          rule.category === 'CALCULATION' ? 'bg-[#e07b00]' : 'bg-[#8899b0]'
                        }`}>{rule.category}</span>
                      </td>
                      <td className="px-4 py-3 text-center font-bold text-[#22c55e]">{rule.passed}</td>
                      <td className="px-4 py-3 text-center font-bold text-[#e53e3e]">{rule.failed}</td>
                      <td className="px-4 py-3 text-center">
                        <span className={`font-bold text-sm ${
                          rule.pass_rate >= 90 ? 'text-[#22c55e]' :
                          rule.pass_rate >= 70 ? 'text-[#e07b00]' : 'text-[#e53e3e]'
                        }`}>{rule.pass_rate}%</span>
                      </td>
                    </tr>
                  ))}
                  {filteredRules.length === 0 && (
                    <tr>
                      <td colSpan={6} className="px-4 py-8 text-center text-[#5a6a85]">No rules match your search.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      {/* Failure Detail Modal */}
      {selectedField && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#0a0f1e]/60 backdrop-blur-sm">
          <Card className="w-full max-w-4xl max-h-[80vh] flex flex-col shadow-2xl">
            <div className="p-4 border-b border-[#e3eaf7] flex items-center justify-between bg-[#f8faff] rounded-t-xl">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-[#fee2e2] rounded-lg">
                  <AlertCircle className="w-5 h-5 text-[#e53e3e]" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-[#1a2340]">Failure Forensics: <code className="font-mono text-[#1a6fcf]">{selectedField}</code></h3>
                  <p className="text-xs text-[#5a6a85]">{failures.length} failure records — invoices that failed this specific validation rule</p>
                </div>
              </div>
              <div className="flex gap-2">
                <Button variant="ghost" onClick={handleExportFailures} size="sm" className="flex items-center gap-2">
                  <Download className="w-4 h-4" /> Export CSV
                </Button>
                <button onClick={() => setSelectedField(null)} className="p-1 hover:bg-[#e3eaf7] rounded-lg transition-colors">
                  <X className="w-6 h-6 text-[#8899b0]" />
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto">
              {loadingFailures ? (
                <div className="p-12 text-center text-[#5a6a85]">Loading forensic logs...</div>
              ) : (
                <table className="w-full text-left text-sm">
                  <thead className="bg-white sticky top-0 border-b border-[#e3eaf7] shadow-sm">
                    <tr>
                      <th className="px-6 py-3 font-semibold text-[#5a6a85]">Invoice #</th>
                      <th className="px-6 py-3 font-semibold text-[#5a6a85]">Date</th>
                      <th className="px-6 py-3 font-semibold text-[#5a6a85]">Error Message</th>
                      <th className="px-6 py-3 font-semibold text-[#5a6a85]">Category</th>
                      <th className="px-6 py-3 font-semibold text-[#5a6a85]">Severity</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#e3eaf7]">
                    {failures.map((f, i) => (
                      <tr key={i} className="hover:bg-[#f8faff]">
                        <td className="px-6 py-4 font-mono font-medium text-[#1a6fcf]">{f.invoice_number}</td>
                        <td className="px-6 py-4 text-[#5a6a85] text-xs">{new Date(f.timestamp).toLocaleString()}</td>
                        <td className="px-6 py-4 text-[#1a2340] text-xs max-w-xs" title={f.message}>{f.message}</td>
                        <td className="px-6 py-4">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase text-white ${
                            f.category === 'COMPLIANCE' ? 'bg-[#1a6fcf]' : f.category === 'CALCULATION' ? 'bg-[#e07b00]' : 'bg-[#8899b0]'
                          }`}>{f.category}</span>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                            f.severity === 'HIGH' ? 'bg-[#fee2e2] text-[#e53e3e]' : 'bg-[#fef3c7] text-[#e07b00]'
                          }`}>{f.severity || 'HIGH'}</span>
                        </td>
                      </tr>
                    ))}
                    {failures.length === 0 && (
                      <tr>
                        <td colSpan={5} className="px-6 py-12 text-center text-[#8899b0]">
                          <CheckCircle2 className="w-8 h-8 text-[#22c55e] mx-auto mb-2" />
                          No failure records found for this field in the selected period.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              )}
            </div>

            <div className="p-4 border-t border-[#e3eaf7] bg-[#f8faff] rounded-b-xl flex justify-end">
              <Button variant="primary" onClick={() => setSelectedField(null)}>Close</Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}
