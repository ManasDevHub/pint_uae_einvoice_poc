import { useState } from 'react'
import Card from '../components/ui/Card'
import Pill from '../components/ui/Pill'
import Button from '../components/ui/Button'
import toast from 'react-hot-toast'

export default function Integrations() {
  const [connectors, setConnectors] = useState([
    { id: 1, name: 'SAP S/4HANA', status: 'Connected', lastSync: '10 mins ago', icon: 'S' },
    { id: 2, name: 'Oracle NetSuite', status: 'Not Configured', lastSync: '-', icon: 'O' },
    { id: 3, name: 'Microsoft Dynamics 365', status: 'Not Configured', lastSync: '-', icon: 'D' },
    { id: 4, name: 'Generic REST API Webhook', status: 'Active', lastSync: '1 min ago', icon: 'W' }
  ])

  const [keys, setKeys] = useState([
    { id: 1, name: 'Production Engine', prefix: 'demo-key-...', created: 'Oct 24, 2025' }
  ])

  const handleConfigure = (c) => {
    if (c.status === 'Not Configured') {
      const idx = connectors.findIndex(x => x.id === c.id)
      const updated = [...connectors]
      updated[idx].status = 'Connected'
      updated[idx].lastSync = 'Just now'
      setConnectors(updated)
      toast.success(`${c.name} connector enabled!`)
    } else {
      toast.success(`${c.name} settings updated!`)
    }
  }

  const handleTest = (c) => {
    const p = toast.loading(`Testing connection to ${c.name}...`)
    setTimeout(() => {
      toast.success('Connection successful! Ping: 24ms', { id: p })
    }, 1500)
  }

  const handleGenerateKey = () => {
    setKeys(k => [...k, { 
      id: Date.now(), 
      name: `New API Key ${k.length + 1}`, 
      prefix: `key-${Math.floor(Math.random()*1000)}-...`, 
      created: 'Just now' 
    }])
    toast.success('New API Key generated successfully')
  }

  const handleRevokeKey = (id) => {
    setKeys(k => k.filter(x => x.id !== id))
    toast.error('API Key revoked', { icon: '⚠️' })
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[#1a2340]">ERP Integrations</h1>
        <p className="text-sm text-[#5a6a85] mt-1">Configure automated invoice data extraction</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {connectors.map((c) => (
          <Card key={c.id} className="p-6">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-lg bg-[#e8f1ff] text-[#1a6fcf] flex items-center justify-center font-bold text-xl shrink-0">
                  {c.icon}
                </div>
                <div>
                  <h3 className="font-semibold text-[#1a2340] text-lg">{c.name}</h3>
                  <div className="flex items-center gap-2 mt-1">
                    <Pill variant={c.status === 'Connected' || c.status === 'Active' ? 'green' : 'gray'}>
                      {c.status}
                    </Pill>
                    <span className="text-xs text-[#5a6a85]">Last sync: {c.lastSync}</span>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="mt-6 flex justify-end gap-2">
              <Button variant="ghost" onClick={() => handleConfigure(c)}>
                {c.status === 'Not Configured' ? 'Enable' : 'Configure'}
              </Button>
              {(c.status === 'Connected' || c.status === 'Active') && (
                <Button variant="primary" onClick={() => handleTest(c)}>Test Connection</Button>
              )}
            </div>
          </Card>
        ))}
      </div>
      
      <Card className="p-6 mt-8">
        <h2 className="text-lg font-semibold text-[#1a2340] mb-4">API Keys</h2>
        <table className="w-full text-left text-sm whitespace-nowrap">
          <thead className="bg-[#f8faff] text-[#5a6a85]">
            <tr>
              <th className="px-4 py-3 font-medium rounded-l-lg border-y border-l border-[#e3eaf7]">Name</th>
              <th className="px-4 py-3 font-medium border-y border-[#e3eaf7]">Key Prefix</th>
              <th className="px-4 py-3 font-medium border-y border-[#e3eaf7]">Created</th>
              <th className="px-4 py-3 font-medium rounded-r-lg border-y border-r border-[#e3eaf7]"></th>
            </tr>
          </thead>
          <tbody>
            {keys.map(k => (
              <tr key={k.id}>
                <td className="px-4 py-4 font-medium text-[#1a2340] border-b border-[#e3eaf7]">{k.name}</td>
                <td className="px-4 py-4 text-[#5a6a85] font-mono border-b border-[#e3eaf7]">{k.prefix}</td>
                <td className="px-4 py-4 text-[#5a6a85] border-b border-[#e3eaf7]">{k.created}</td>
                <td className="px-4 py-4 text-right border-b border-[#e3eaf7]">
                  <Button variant="danger" onClick={() => handleRevokeKey(k.id)}>Revoke</Button>
                </td>
              </tr>
            ))}
            {keys.length === 0 && (
              <tr><td colSpan={4} className="px-4 py-4 text-center text-[#8899b0]">No API keys found.</td></tr>
            )}
          </tbody>
        </table>
        <div className="mt-4">
          <Button variant="ghost" onClick={handleGenerateKey}>Generate New Key</Button>
        </div>
      </Card>
    </div>
  )
}
