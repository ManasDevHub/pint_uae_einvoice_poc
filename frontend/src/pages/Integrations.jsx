import { useState, useEffect } from 'react'
import Card from '../components/ui/Card'
import Pill from '../components/ui/Pill'
import Button from '../components/ui/Button'
import toast from 'react-hot-toast'
import { API_BASE } from '../constants/api'
import { API_HEADERS } from '../constants/apiHelpers'
import { 
  Building2, 
  Globe, 
  FileCode, 
  CloudUpload, 
  Webhook, 
  CheckCircle2, 
  AlertCircle, 
  ExternalLink,
  Copy,
  Plus,
  Trash2,
  Table as TableIcon,
  BookOpen,
  Activity,
  ChevronRight,
  Settings as SettingsIcon,
  Key as KeyIcon
} from 'lucide-react'

const ERP_TEMPLATES = [
  {
    id: 'SAP',
    name: 'SAP S/4HANA',
    icon: <Building2 className="w-6 h-6" />,
    color: '#0070f3',
    description: 'Connect via SM59 HTTP destination. Invoice posts trigger real-time validation.',
    modes: ['api_push'],
  },
  {
    id: 'NETSUITE',
    name: 'Oracle NetSuite',
    icon: <Globe className="w-6 h-6" />,
    color: '#e84034',
    description: 'SuiteScript UserEventScript calls our API on invoice creation.',
    modes: ['api_push', 'api_pull'],
  },
  {
    id: 'DYNAMICS',
    name: 'Microsoft Dynamics 365',
    icon: <SettingsIcon className="w-6 h-6" />,
    color: '#00bcf2',
    description: 'Power Automate flow sends invoice on record creation.',
    modes: ['api_push'],
  },
  {
    id: 'SFTP',
    name: 'SFTP File Transfer',
    icon: <CloudUpload className="w-6 h-6" />,
    color: '#7c3aed',
    description: 'ERP drops XML/CSV files. Platform polls and processes automatically.',
    modes: ['sftp'],
  },
  {
    id: 'WEBHOOK',
    name: 'Generic Webhook',
    icon: <Webhook className="w-6 h-6" />,
    color: '#059669',
    description: 'Any system sends a POST to your unique webhook URL. Instant processing.',
    modes: ['webhook'],
  },
]

export default function Integrations() {
  const [activeTab, setActiveTab] = useState('connections')
  const [connections, setConnections] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedConn, setSelectedConn] = useState(null)
  const [showModal, setShowModal] = useState(false)
  const [modalTab, setModalTab] = useState('setup')
  const [systemKeys, setSystemKeys] = useState([])
  const [isAddingKey, setIsAddingKey] = useState(false)
  const [newKeyName, setNewKeyName] = useState('')
  const [generatedKey, setGeneratedKey] = useState(null)
  const [formData, setFormData] = useState({})
  const [instructions, setInstructions] = useState(null)

  useEffect(() => {
    fetchConnections()
    fetchSystemKeys()
  }, [])

  const fetchConnections = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/integrations/connections`, {
        headers: API_HEADERS
      })
      if (!res.ok) throw new Error('Unauthorized')
      const data = await res.json()
      setConnections(Array.isArray(data) ? data : [])
    } catch (err) {
      console.error('Integrations load error:', err)
      setConnections([])
      toast.error('Failed to load connections')
    } finally {
      setLoading(false)
    }
  }

  const fetchSystemKeys = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/system/keys`, { headers: API_HEADERS })
      const data = await res.json()
      setSystemKeys(Array.isArray(data) ? data : [])
    } catch (err) {
      console.error('Keys error:', err)
    }
  }

  const handleGenerateKey = async () => {
    if (!newKeyName) return toast.error('Key name is required')
    try {
      const res = await fetch(`${API_BASE}/api/v1/system/keys`, {
        method: 'POST',
        headers: API_HEADERS,
        body: JSON.stringify({ name: newKeyName })
      })
      const data = await res.json()
      setGeneratedKey(data.key)
      setNewKeyName('')
      fetchSystemKeys()
      toast.success('System API Key generated')
    } catch (err) {
      toast.error('Failed to generate key')
    }
  }

  const handleRevokeKey = async (id) => {
    if (!confirm('Revoke this key? It will immediately stop working.')) return
    try {
      await fetch(`${API_BASE}/api/v1/system/keys/${id}`, { method: 'DELETE', headers: API_HEADERS })
      fetchSystemKeys()
      toast.success('Key revoked')
    } catch (err) {
      toast.error('Revoke failed')
    }
  }

  const handleOpenConfigure = async (template) => {
    const existing = connections.find(c => c.erp_type === template.id)
    if (existing) {
      setSelectedConn(existing)
      setFormData(existing)
      fetchInstructions(existing.id)
    } else {
      setSelectedConn({ ...template, isNew: true })
      setFormData({ erp_type: template.id, integration_mode: template.modes[0], display_name: template.name })
      setInstructions(null)
    }
    setModalTab('setup')
    setShowModal(true)
  }

  const fetchInstructions = async (id) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/integrations/connections/${id}/instructions`, {
        headers: API_HEADERS
      })
      const data = await res.json()
      setInstructions(data)
    } catch (err) {
      console.error('Instructions error:', err)
    }
  }

  const handleSave = async () => {
    const method = selectedConn?.isNew ? 'POST' : 'PUT'
    const url = selectedConn?.isNew 
      ? '/api/v1/integrations/connections' 
      : `/api/v1/integrations/connections/${selectedConn.id}`

    try {
      const res = await fetch(url, {
        method,
        headers: API_HEADERS,
        body: JSON.stringify(formData)
      })
      if (!res.ok) throw new Error('Save failed')
      const data = await res.json()
      toast.success('Integration settings saved')
      fetchConnections()
      if (selectedConn?.isNew) {
        setSelectedConn(data)
        fetchInstructions(data.id)
      }
    } catch (err) {
      toast.error('Save failed')
    }
  }

  const handleTest = async (id) => {
    const p = toast.loading('Testing connection...')
    try {
      const res = await fetch(`${API_BASE}/api/v1/integrations/connections/${id}/test`, { 
        method: 'POST',
        headers: API_HEADERS
      })
      const data = await res.json()
      if (data.status === 'ok') {
        toast.success(data.message, { id: p })
        fetchConnections()
      } else {
        toast.error(data.message, { id: p })
      }
    } catch (err) {
      toast.error('Test request failed', { id: p })
    }
  }

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text)
    toast.success('Copied to clipboard')
  }

  const handleToggleStatus = async (id, currentStatus) => {
    const newStatus = currentStatus === 'active' ? 'paused' : 'active'
    try {
      const res = await fetch(`${API_BASE}/api/v1/integrations/connections/${id}`, {
        method: 'PUT',
        headers: API_HEADERS,
        body: JSON.stringify({ status: newStatus })
      })
      if (!res.ok) throw new Error('Update failed')
      toast.success(`Connection ${newStatus === 'active' ? 'activated' : 'deactivated'}`)
      fetchConnections()
      // Update selectedConn if modal is open
      if (selectedConn && selectedConn.id === id) {
        setSelectedConn(prev => ({ ...prev, status: newStatus }))
      }
    } catch (err) {
      toast.error('Failed to change status')
    }
  }

  const handleResetConnection = async (id) => {
    if (!confirm('Completely reset this configuration? All credentials and mapping will be lost.')) return
    try {
      const res = await fetch(`${API_BASE}/api/v1/integrations/connections/${id}`, {
        method: 'DELETE',
        headers: API_HEADERS
      })
      if (!res.ok) throw new Error('Delete failed')
      toast.success('Configuration reset successful')
      setShowModal(false)
      fetchConnections()
    } catch (err) {
      toast.error('Failed to reset configuration')
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[#1a2340]">ERP Integrations</h1>
          <p className="text-sm text-[#5a6a85] mt-1">Enterprise-grade automation for your financial supply chain</p>
        </div>
        <div className="flex bg-[#f1f5f9] p-1 rounded-lg">
          <button 
            onClick={() => setActiveTab('connections')}
            className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${activeTab === 'connections' ? 'bg-white shadow-sm text-[#1a6fcf]' : 'text-[#5a6a85]'}`}
          >
            Connections
          </button>
          <button 
            onClick={() => setActiveTab('keys')}
            className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${activeTab === 'keys' ? 'bg-white shadow-sm text-[#1a6fcf]' : 'text-[#5a6a85]'}`}
          >
            System Keys
          </button>
        </div>
      </div>

      {activeTab === 'connections' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {ERP_TEMPLATES.map((tpl) => {
            const conn = connections.find(c => c.erp_type === tpl.id)
            return (
              <Card key={tpl.id} className="p-6 group relative overflow-hidden border-[#e3eaf7] hover:border-[#1a6fcf] transition-all">
                <div className="flex items-start justify-between">
                  <div 
                    className="p-3 rounded-xl transition-colors"
                    style={{ backgroundColor: `${tpl.color}15`, color: tpl.color }}
                  >
                    {tpl.icon}
                  </div>
                  {conn ? (
                    <Pill variant={conn.status === 'active' ? 'green' : conn.status === 'error' ? 'red' : 'gray'}>
                      {(conn.status || '').replace('_', ' ')}
                    </Pill>
                  ) : (
                    <span className="text-xs text-[#8899b0] bg-[#f8faff] px-2 py-1 rounded">Not Configured</span>
                  )}
                </div>
                
                <h3 className="mt-4 font-bold text-[#1a2340] text-lg">{tpl.name}</h3>
                <p className="mt-2 text-sm text-[#5a6a85] leading-relaxed line-clamp-2">
                  {tpl.description}
                </p>

                <div className="mt-6 flex items-center justify-between pt-4 border-t border-[#f1f5f9]">
                  <div className="text-[10px] text-[#8899b0] uppercase tracking-wider font-semibold">
                    {conn?.last_sync_at ? `Last sync: ${new Date(conn.last_sync_at).toLocaleDateString()}` : 'No sync history'}
                  </div>
                  <Button variant="ghost" onClick={() => handleOpenConfigure(tpl)}>
                    Configure <ChevronRight className="w-4 h-4 ml-1" />
                  </Button>
                </div>
              </Card>
            )
          })}
        </div>
      ) : (
        <div className="space-y-6">
          <Card className="p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="font-bold text-[#1a2340] text-lg">System API Keys</h3>
                <p className="text-sm text-[#5a6a85]">Use these keys to authenticate external ERP calls to the PINT AE engine.</p>
              </div>
              <Button variant="primary" onClick={() => setIsAddingKey(true)}>
                <Plus className="w-4 h-4 mr-2" /> Generate Key
              </Button>
            </div>

            {isAddingKey && (
              <div className="mb-6 p-4 bg-[#f8faff] border border-[#d1d5db] rounded-xl flex items-center gap-3 animate-in slide-in-from-top-2">
                <input 
                  type="text" 
                  value={newKeyName} 
                  onChange={e => setNewKeyName(e.target.value)}
                  placeholder="Key name (e.g. Oracle Production)"
                  className="flex-1 px-3 py-2 border rounded-lg text-sm outline-none focus:border-[#1a6fcf]"
                />
                <Button variant="primary" onClick={handleGenerateKey}>Create</Button>
                <Button variant="ghost" onClick={() => setIsAddingKey(false)}>Cancel</Button>
              </div>
            )}

            {generatedKey && (
              <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-xl animate-in zoom-in-95">
                <p className="text-sm font-bold text-green-800 mb-2">New Key Generated (Save this now!):</p>
                <div className="flex items-center gap-2 bg-white p-2 rounded border border-green-100 font-mono text-xs overflow-x-auto">
                  {generatedKey}
                  <button onClick={() => { navigator.clipboard.writeText(generatedKey); toast.success('Copied!') }} className="ml-auto p-1 hover:bg-gray-100 rounded">
                    <Copy className="w-4 h-4 text-[#1a6fcf]" />
                  </button>
                </div>
                <button onClick={() => setGeneratedKey(null)} className="mt-2 text-xs text-green-700 underline">Dismiss</button>
              </div>
            )}

            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm whitespace-nowrap">
                <thead className="bg-[#f8faff] text-[#5a6a85] text-[11px] uppercase tracking-wider font-bold">
                  <tr>
                    <th className="px-4 py-3">Key Name</th>
                    <th className="px-4 py-3">Prefix</th>
                    <th className="px-4 py-3">Created</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#e3eaf7]">
                  {systemKeys.length === 0 ? (
                    <tr><td colSpan={5} className="px-4 py-10 text-center text-[#8899b0]">No keys generated yet.</td></tr>
                  ) : systemKeys.map(k => (
                    <tr key={k.id} className="hover:bg-[#f8faff]/50">
                      <td className="px-4 py-3 font-semibold text-[#1a2340]">{k.name}</td>
                      <td className="px-4 py-3"><code className="text-xs bg-gray-100 px-1 rounded">{k.key_prefix}</code></td>
                      <td className="px-4 py-3 text-[#5a6a85] text-xs">{new Date(k.created_at).toLocaleDateString()}</td>
                      <td className="px-4 py-3">
                        <Pill variant={k.is_active ? 'green' : 'gray'}>{k.is_active ? 'ACTIVE' : 'REVOKED'}</Pill>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button onClick={() => handleRevokeKey(k.id)} className="text-red-500 hover:bg-red-50 p-1.5 rounded-lg transition-colors">
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}

      {/* MODAL OVERLAY */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col animate-in fade-in zoom-in duration-200">
            {/* Modal Header */}
            <div className="p-6 border-b border-[#f1f5f9] flex items-center justify-between bg-[#f8faff]">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-lg bg-white shadow-sm flex items-center justify-center text-[#1a6fcf]">
                  <SettingsIcon className="w-6 h-6" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-[#1a2340]">Configure {selectedConn?.name}</h2>
                  <p className="text-xs text-[#5a6a85]">{selectedConn?.id} {selectedConn?.isNew ? 'New Installation' : 'Active Connection'}</p>
                </div>
              </div>
              <button onClick={() => setShowModal(false)} className="text-[#8899b0] hover:text-[#1a2340]">&times;</button>
            </div>

            {/* Modal Tabs */}
            <div className="flex border-b border-[#f1f5f9] px-6">
              {[
                { id: 'setup', label: 'Setup', icon: <SettingsIcon className="w-4 h-4" /> },
                { id: 'mapping', label: 'Field Mapping', icon: <TableIcon className="w-4 h-4" /> },
                { id: 'guide', label: 'Integration Guide', icon: <BookOpen className="w-4 h-4" /> },
                { id: 'test', label: 'Live Test', icon: <Activity className="w-4 h-4" /> },
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setModalTab(tab.id)}
                  className={`px-6 py-4 text-sm font-semibold flex items-center gap-2 border-b-2 transition-all ${modalTab === tab.id ? 'border-[#1a6fcf] text-[#1a6fcf]' : 'border-transparent text-[#8899b0] hover:text-[#1a2340]'}`}
                >
                  {tab.icon} {tab.label}
                </button>
              ))}
            </div>

            {/* Modal Content */}
            <div className="p-8 flex-1 overflow-y-auto">
              {modalTab === 'setup' && (
                <div className="space-y-6">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <label className="text-xs font-bold text-[#1a2340] uppercase">Integration Mode</label>
                      <select 
                        value={formData.integration_mode} 
                        onChange={e => setFormData({...formData, integration_mode: e.target.value})}
                        className="w-full p-3 bg-[#f8faff] border border-[#e3eaf7] rounded-lg focus:ring-2 focus:ring-[#1a6fcf] outline-none"
                      >
                        <option value="api_push">REST API Push (Real-time)</option>
                        <option value="sftp">SFTP Polling (Batch)</option>
                        <option value="webhook">Inbound Webhook</option>
                        <option value="api_pull">Outbound API Pull</option>
                      </select>
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs font-bold text-[#1a2340] uppercase">Display Name</label>
                      <input 
                        type="text" 
                        value={formData.display_name} 
                        onChange={e => setFormData({...formData, display_name: e.target.value})}
                        className="w-full p-3 bg-[#f8faff] border border-[#e3eaf7] rounded-lg focus:ring-2 focus:ring-[#1a6fcf] outline-none"
                      />
                    </div>
                  </div>

                  {formData.integration_mode === 'sftp' && (
                    <Card className="p-4 bg-[#f8faff] border-dashed space-y-4">
                      <div className="grid grid-cols-3 gap-4">
                        <div className="col-span-2">
                          <label className="text-[10px] font-bold text-[#5a6a85]">SFTP HOST</label>
                          <input type="text" value={formData.sftp_host || ''} onChange={e => setFormData({...formData, sftp_host: e.target.value})} className="w-full mt-1 p-2 bg-white border border-[#e3eaf7] rounded" />
                        </div>
                        <div>
                          <label className="text-[10px] font-bold text-[#5a6a85]">PORT</label>
                          <input type="number" value={formData.sftp_port || 22} onChange={e => setFormData({...formData, sftp_port: e.target.value})} className="w-full mt-1 p-2 bg-white border border-[#e3eaf7] rounded" />
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="text-[10px] font-bold text-[#5a6a85]">USERNAME</label>
                          <input type="text" value={formData.sftp_username || ''} onChange={e => setFormData({...formData, sftp_username: e.target.value})} className="w-full mt-1 p-2 bg-white border border-[#e3eaf7] rounded" />
                        </div>
                        <div>
                          <label className="text-[10px] font-bold text-[#5a6a85]">POLL FREQUENCY</label>
                          <select value={formData.poll_interval_minutes || 15} onChange={e => setFormData({...formData, poll_interval_minutes: parseInt(e.target.value)})} className="w-full mt-1 p-2 bg-white border border-[#e3eaf7] rounded">
                             <option value="5">Every 5 Minutes</option>
                             <option value="15">Every 15 Minutes</option>
                             <option value="60">Hourly</option>
                             <option value="1440">Daily</option>
                          </select>
                        </div>
                      </div>
                      <div className="space-y-1">
                        <label className="text-[10px] font-bold text-[#5a6a85]">RSA PRIVATE KEY (PEM)</label>
                        <textarea 
                          placeholder="-----BEGIN RSA PRIVATE KEY-----..." 
                          className="w-full h-32 p-2 font-mono text-[10px] bg-white border border-[#e3eaf7] rounded outline-none focus:border-[#1a6fcf]"
                          value={formData.sftp_private_key || (formData.encrypted_credentials ? JSON.parse(formData.encrypted_credentials).sftp_private_key : '')}
                          onChange={e => {
                            const creds = formData.encrypted_credentials ? JSON.parse(formData.encrypted_credentials) : {};
                            creds.sftp_private_key = e.target.value;
                            setFormData({...formData, encrypted_credentials: JSON.stringify(creds), sftp_private_key: e.target.value});
                          }}
                        />
                      </div>
                    </Card>
                  )}

                  {formData.integration_mode === 'webhook' && (
                    <div className="space-y-4">
                      <div className="p-4 bg-[#e8f1ff] rounded-xl border border-[#1a6fcf]/20 flex items-center justify-between">
                        <div>
                          <p className="text-[10px] font-bold text-[#1a6fcf] uppercase">Your Unique Webhook URL</p>
                          <code className="text-xs font-mono text-[#1a2340]">{formData.webhook_url || 'https://adamas-einvoice.koyeb.app/api/v1/integrations/webhook/...'}</code>
                        </div>
                        <Button variant="ghost" size="sm" onClick={() => copyToClipboard(formData.webhook_url)}><Copy className="w-4 h-4" /></Button>
                      </div>
                      <div className="space-y-1">
                        <label className="text-xs font-bold text-[#1a2340] uppercase">Inbound HMAC Secret</label>
                        <input 
                          type="text" 
                          placeholder="Your custom secret key..." 
                          value={formData.webhook_secret || ''} 
                          onChange={e => setFormData({...formData, webhook_secret: e.target.value})}
                          className="w-full p-3 bg-[#f8faff] border border-[#e3eaf7] rounded-lg focus:ring-2 focus:ring-[#1a6fcf] outline-none"
                        />
                        <p className="text-[10px] text-[#8899b0]">Your ERP must send this in the `X-Webhook-Signature` header (HMAC-SHA256).</p>
                      </div>
                    </div>
                  )}

                  {formData.integration_mode === 'api_push' && !['sftp', 'webhook', 'api_pull'].includes(formData.integration_mode) && (
                    <div className="p-4 bg-[#e8f1ff] rounded-xl border border-[#1a6fcf]/20 flex items-center justify-between">
                      <div>
                        <p className="text-[10px] font-bold text-[#1a6fcf] uppercase">Your Validation Endpoint</p>
                        <code className="text-xs font-mono text-[#1a2340]">https://adamas-einvoice.koyeb.app/api/v1/validate-invoice</code>
                      </div>
                      <Button variant="ghost" size="sm" onClick={() => copyToClipboard('https://adamas-einvoice.koyeb.app/api/v1/validate-invoice')}><Copy className="w-4 h-4" /></Button>
                    </div>
                  )}

                  <div className="flex justify-between items-center pt-4 border-t border-[#f1f5f9]">
                    {!selectedConn?.isNew && (
                      <div className="flex gap-2">
                         <Button 
                           variant="ghost" 
                           className={selectedConn?.status === 'active' ? 'text-amber-600 hover:bg-amber-50' : 'text-green-600 hover:bg-green-50'}
                           onClick={() => handleToggleStatus(selectedConn.id, selectedConn.status)}
                         >
                           {selectedConn?.status === 'active' ? 'Deactivate Connection' : 'Activate Connection'}
                         </Button>
                         <Button 
                           variant="ghost" 
                           className="text-red-500 hover:bg-red-50"
                           onClick={() => handleResetConnection(selectedConn.id)}
                         >
                           Reset Configuration
                         </Button>
                      </div>
                    )}
                    <div className="flex gap-2 ml-auto">
                      <Button variant="ghost" onClick={() => setShowModal(false)}>Cancel</Button>
                      <Button variant="primary" onClick={handleSave}>Save Configuration</Button>
                    </div>
                  </div>
                </div>
              )}

              {modalTab === 'mapping' && (
                <div className="space-y-4">
                   <div className="flex items-center justify-between mb-2">
                      <h4 className="text-sm font-bold text-[#1a2340]">Schema Translation Map</h4>
                      <Button variant="ghost" size="sm" onClick={() => setFormData({...formData, field_mapping: {...(formData.field_mapping || {}), '': ''}})}>
                        <Plus className="w-4 h-4 mr-1" /> Add Mapping
                      </Button>
                   </div>
                   <div className="border border-[#e3eaf7] rounded-xl overflow-hidden">
                      <table className="w-full text-sm">
                        <thead className="bg-[#f8faff] border-b border-[#e3eaf7]">
                          <tr>
                            <th className="px-4 py-2 text-[#5a6a85] font-semibold">ERP Data Column</th>
                            <th className="px-4 py-2 text-[#5a6a85] font-semibold text-center"><ChevronRight className="w-4 h-4 inline" /></th>
                            <th className="px-4 py-2 text-[#5a6a85] font-semibold">PINT AE Standard Field</th>
                            <th className="px-4 py-2 w-10"></th>
                          </tr>
                        </thead>
                        <tbody>
                          {Object.entries(formData.field_mapping || {}).map(([key, val], idx) => (
                            <tr key={idx} className="border-b border-[#f1f5f9] last:border-0 hover:bg-[#f8faff]/50">
                              <td className="p-2 px-4">
                                <input 
                                  className="w-full bg-transparent outline-none focus:text-[#1a6fcf]" 
                                  value={key} 
                                  onChange={e => {
                                    const nm = {...formData.field_mapping};
                                    delete nm[key];
                                    nm[e.target.value] = val;
                                    setFormData({...formData, field_mapping: nm});
                                  }}
                                />
                              </td>
                              <td className="p-2 text-center text-[#8899b0]">→</td>
                              <td className="p-2 px-4">
                                <select 
                                  className="w-full bg-transparent outline-none"
                                  value={val}
                                  onChange={e => {
                                    const nm = {...formData.field_mapping};
                                    nm[key] = e.target.value;
                                    setFormData({...formData, field_mapping: nm});
                                  }}
                                >
                                  <option value="invoice_number">invoice_number</option>
                                  <option value="invoice_date">invoice_date</option>
                                  <option value="seller_trn">seller_trn</option>
                                  <option value="buyer_trn">buyer_trn</option>
                                  <option value="total_with_tax">total_with_tax</option>
                                </select>
                              </td>
                              <td className="p-2">
                                <button className="text-[#8899b0] hover:text-red-500" onClick={() => {
                                  const nm = {...formData.field_mapping};
                                  delete nm[key];
                                  setFormData({...formData, field_mapping: nm});
                                }}><Trash2 className="w-4 h-4" /></button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                   </div>
                   <div className="flex justify-end pt-4">
                      <Button variant="primary" onClick={handleSave}>Update Mapping</Button>
                   </div>
                </div>
              )}

              {modalTab === 'guide' && (
                <div className="space-y-6 max-h-[50vh] overflow-y-auto pr-2 custom-scrollbar">
                   {instructions ? (
                     <>
                       <div className="space-y-4">
                          {instructions.steps?.map(s => (
                            <div key={s.step} className="flex gap-4">
                              <div className="w-6 h-6 rounded-full bg-[#1a6fcf] text-white flex items-center justify-center text-[10px] font-bold shrink-0 mt-1">{s.step}</div>
                              <div>
                                <h5 className="font-bold text-[#1a2340] text-sm">{s.title}</h5>
                                <p className="text-xs text-[#5a6a85] mt-1">{s.detail}</p>
                              </div>
                            </div>
                          ))}
                       </div>
                       
                       {instructions.sample_abap && (
                         <div className="mt-8 space-y-2">
                            <div className="flex items-center justify-between">
                              <label className="text-[10px] font-bold text-[#5a6a85] uppercase">Target ABAP Logic</label>
                              <button onClick={() => copyToClipboard(instructions.sample_abap)} className="text-[10px] text-[#1a6fcf] flex items-center gap-1 hover:underline"><Copy className="w-3 h-3" /> Copy Code</button>
                            </div>
                            <pre className="p-4 bg-[#1a2340] text-blue-100 rounded-xl text-[11px] font-mono overflow-x-auto">
                              {instructions.sample_abap}
                            </pre>
                         </div>
                       )}

                       {instructions.sample_suitescript && (
                         <div className="mt-8 space-y-2">
                             <div className="flex items-center justify-between">
                              <label className="text-[10px] font-bold text-[#5a6a85] uppercase">SuiteScript 2.1 Sample</label>
                              <button onClick={() => copyToClipboard(instructions.sample_suitescript)} className="text-[10px] text-[#1a6fcf] flex items-center gap-1 hover:underline"><Copy className="w-3 h-3" /> Copy Code</button>
                            </div>
                            <pre className="p-4 bg-[#1a2340] text-blue-100 rounded-xl text-[11px] font-mono overflow-x-auto">
                              {instructions.sample_suitescript}
                            </pre>
                         </div>
                       )}
                     </>
                   ) : (
                     <div className="flex flex-col items-center justify-center py-12 text-center">
                        <BookOpen className="w-12 h-12 text-[#e3eaf7] mb-4" />
                        <h4 className="font-bold text-[#1a2340]">Guide unavailable</h4>
                        <p className="text-xs text-[#5a6a85]">Please save the setup first to generate your custom integration docs.</p>
                     </div>
                   )}
                </div>
              )}

              {modalTab === 'test' && (
                <div className="space-y-6">
                   <div className="flex items-center justify-between p-6 bg-[#f8faff] rounded-2xl border border-[#e3eaf7]">
                      <div>
                        <h4 className="font-bold text-[#1a2340]">Status: {selectedConn?.status === 'active' ? 'Operational' : 'Idle'}</h4>
                        <p className="text-xs text-[#5a6a85] mt-1">Validate your ERP handshake and see live data flow.</p>
                      </div>
                      <Button variant="primary" onClick={() => handleTest(selectedConn.id)}>
                        <Activity className="w-4 h-4 mr-2" /> Start Connection Test
                      </Button>
                   </div>

                   <div className="space-y-4">
                      <h5 className="text-xs font-bold text-[#5a6a85] uppercase tracking-wider">Last 5 Invoices via this path</h5>
                      <div className="text-center py-12 border-2 border-dashed border-[#f1f5f9] rounded-2xl">
                        <AlertCircle className="w-10 h-10 text-[#e3eaf7] mx-auto mb-2" />
                        <p className="text-sm text-[#8899b0]">No live invoices detected yet for this connection.</p>
                      </div>
                   </div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-6 border-t border-[#f1f5f9] bg-[#f8faff] flex items-center justify-between">
              <div className="flex items-center gap-2">
                 <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                 <span className="text-[10px] text-[#5a6a85] font-medium uppercase tracking-tight">System Node: Koyeb-Dubai-01</span>
              </div>
              <Button variant="ghost" onClick={() => setShowModal(false)} size="sm">Close Panel</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
