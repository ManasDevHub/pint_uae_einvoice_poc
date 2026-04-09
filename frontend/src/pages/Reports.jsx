import { useState, useEffect } from 'react'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import DonutChart from '../components/charts/DonutChart'
import { API_BASE } from '../constants/api'
import { downloadCsv, API_HEADERS } from '../constants/apiHelpers'
import { Download, FileBarChart2, CheckCircle2, XCircle, RefreshCw } from 'lucide-react'
import toast from 'react-hot-toast'

const PERIODS = [
  { key: 'daily', label: 'Today', icon: '📅' },
  { key: 'monthly', label: 'Monthly', icon: '📆' },
  { key: 'quarterly', label: 'Quarterly', icon: '🗓️' },
  { key: 'yearly', label: 'Yearly', icon: '📊' },
  { key: 'all', label: 'All Time', icon: '🔍' },
]

export default function Reports() {
  const [period, setPeriod] = useState('monthly')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  useEffect(() => {
    loadReport()
  }, [period])

  const loadReport = async () => {
    try {
      setLoading(true)
      const res = await fetch(`${API_BASE}/api/v1/reports?period=${period}`, {
        headers: API_HEADERS
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || err.message || `Failed to load report (${res.status})`)
      }
      setData(await res.json())
    } catch (e) {
      toast.error(e.message)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  const handleExport = async () => {
    try {
      const filename = `uae_pint_ae_report_${period}_${new Date().toISOString().slice(0,10)}.csv`
      await downloadCsv(`${API_BASE}/api/v1/reports/export?period=${period}`, filename)
      toast.success('Report exported successfully')
    } catch (e) {
      toast.error(`Export failed: ${e.message}`)
    }
  }

  const handleRefresh = () => {
    setRefreshing(true)
    loadReport()
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="text-center text-[#5a6a85]">
          <FileBarChart2 className="w-12 h-12 mx-auto mb-4 opacity-40 animate-pulse" />
          <p>Generating report...</p>
        </div>
      </div>
    )
  }

  const summary = data?.summary || {}
  const passRate = summary.pass_rate || 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-[#1a2340]">Reports</h1>
          <p className="text-sm text-[#5a6a85] mt-1">
            {data?.period_label ? `Period: ${data.period_label}` : 'Date-filtered compliance reports'}
            {data?.generated_at && ` · Generated ${new Date(data.generated_at).toLocaleString()}`}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleRefresh}
            className={`p-2 rounded-lg text-[#5a6a85] hover:bg-[#f0f4ff] transition-colors ${refreshing ? 'animate-spin' : ''}`}
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <Button variant="primary" onClick={handleExport} className="flex items-center gap-2">
            <Download className="w-4 h-4" />
            Export CSV
          </Button>
        </div>
      </div>

      {/* Period Selector */}
      <div className="flex flex-wrap gap-3">
        {PERIODS.map(p => (
          <button
            key={p.key}
            onClick={() => setPeriod(p.key)}
            className={`flex items-center gap-2 px-4 py-3 rounded-xl border-2 text-sm font-semibold transition-all ${
              period === p.key
                ? 'border-[#1a6fcf] bg-[#f0f4ff] text-[#1a6fcf]'
                : 'border-[#e3eaf7] bg-white text-[#5a6a85] hover:border-[#1a6fcf]/40'
            }`}
          >
            <span className="text-base">{p.icon}</span>
            {p.label}
          </button>
        ))}
      </div>

      {/* KPI Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="p-5 text-center">
          <div className="text-xs font-semibold text-[#8899b0] uppercase tracking-wider mb-2">Total Invoices</div>
          <div className="text-4xl font-bold text-[#1a2340]">{summary.total_invoices || 0}</div>
        </Card>
        <Card className="p-5 text-center">
          <div className="text-xs font-semibold text-[#8899b0] uppercase tracking-wider mb-2">Pass Rate</div>
          <div className={`text-4xl font-bold ${passRate >= 80 ? 'text-[#22c55e]' : passRate >= 60 ? 'text-[#e07b00]' : 'text-[#e53e3e]'}`}>
            {passRate}%
          </div>
        </Card>
        <Card className="p-5 text-center">
          <div className="flex items-center justify-center gap-1 text-xs font-semibold text-[#8899b0] uppercase tracking-wider mb-2">
            <CheckCircle2 className="w-3.5 h-3.5 text-[#22c55e]" /> Valid
          </div>
          <div className="text-4xl font-bold text-[#22c55e]">{summary.valid || 0}</div>
        </Card>
        <Card className="p-5 text-center">
          <div className="flex items-center justify-center gap-1 text-xs font-semibold text-[#8899b0] uppercase tracking-wider mb-2">
            <XCircle className="w-3.5 h-3.5 text-[#e53e3e]" /> Failed
          </div>
          <div className="text-4xl font-bold text-[#e53e3e]">{summary.failed || 0}</div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_1.5fr] gap-6">
        {/* Category Breakdown */}
        <Card className="p-6">
          <h2 className="text-sm font-semibold text-[#8899b0] uppercase tracking-wider mb-4">Error Categories</h2>
          {data?.by_category?.length > 0 ? (
            <DonutChart data={data.by_category} />
          ) : (
            <div className="h-48 flex flex-col items-center justify-center text-[#8899b0]">
              <CheckCircle2 className="w-10 h-10 text-[#22c55e] mb-2" />
              <p className="text-sm">No errors in this period</p>
            </div>
          )}
        </Card>

        {/* Top Failing Rules */}
        <Card className="p-6">
          <h2 className="text-sm font-semibold text-[#8899b0] uppercase tracking-wider mb-4">Top Failing Rules</h2>
          {data?.top_failing_rules?.length > 0 ? (
            <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
              {data.top_failing_rules.map((rule, i) => (
                <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-[#f8faff] border border-[#e3eaf7]">
                  <div className="w-6 h-6 rounded-full bg-[#e53e3e]/10 text-[#e53e3e] text-xs font-bold flex items-center justify-center flex-shrink-0">
                    {i + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <code className="text-xs font-mono text-[#1a6fcf] bg-white border border-[#e3eaf7] px-1.5 py-0.5 rounded">
                      {rule.field}
                    </code>
                    <p className="text-xs text-[#5a6a85] mt-0.5 truncate" title={rule.message}>{rule.message}</p>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <div className="text-sm font-bold text-[#e53e3e]">{rule.count}</div>
                    <div className="text-xs text-[#8899b0]">{rule.fail_rate}% fail</div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="h-48 flex flex-col items-center justify-center text-[#8899b0]">
              <CheckCircle2 className="w-10 h-10 text-[#22c55e] mb-2" />
              <p className="text-sm">No rule failures in this period</p>
            </div>
          )}
        </Card>
      </div>

      {/* Daily Breakdown Table */}
      {data?.daily_breakdown?.length > 0 && (
        <Card className="p-6">
          <h2 className="text-sm font-semibold text-[#8899b0] uppercase tracking-wider mb-4">Invoices by Day</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-[#f8faff] text-[#5a6a85]">
                <tr>
                  <th className="px-4 py-3 font-medium">Date</th>
                  <th className="px-4 py-3 font-medium text-center">Total</th>
                  <th className="px-4 py-3 font-medium text-center">✅ Passed</th>
                  <th className="px-4 py-3 font-medium text-center">❌ Failed</th>
                  <th className="px-4 py-3 font-medium text-center">Pass Rate</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#e3eaf7]">
                {data.daily_breakdown.map((row, i) => {
                  const rate = row.total > 0 ? Math.round(row.passed / row.total * 100) : 0
                  return (
                    <tr key={i} className="hover:bg-[#f8faff]">
                      <td className="px-4 py-3 font-medium text-[#1a2340]">{row.date}</td>
                      <td className="px-4 py-3 text-center">{row.total}</td>
                      <td className="px-4 py-3 text-center text-[#22c55e] font-semibold">{row.passed}</td>
                      <td className="px-4 py-3 text-center text-[#e53e3e] font-semibold">{row.failed}</td>
                      <td className="px-4 py-3 text-center">
                        <span className={`font-bold ${rate >= 80 ? 'text-[#22c55e]' : rate >= 60 ? 'text-[#e07b00]' : 'text-[#e53e3e]'}`}>
                          {rate}%
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Empty state when no data at all */}
      {data && summary.total_invoices === 0 && (
        <Card className="p-12 text-center">
          <FileBarChart2 className="w-12 h-12 mx-auto mb-4 text-[#8899b0] opacity-40" />
          <h3 className="text-lg font-semibold text-[#1a2340] mb-2">No data for this period</h3>
          <p className="text-sm text-[#5a6a85]">Submit some invoices via Validate or Bulk Upload, then come back to see your compliance report.</p>
        </Card>
      )}
    </div>
  )
}
