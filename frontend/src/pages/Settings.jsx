import { useState } from 'react'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import toast from 'react-hot-toast'

export default function Settings() {
  const [profile, setProfile] = useState({
    companyName: 'Adamas Tech Consulting',
    trn: '100234567890003',
    address: 'Dubai Silicon Oasis, DDP, Building A2'
  })

  const [apiConfig, setApiConfig] = useState({
    cors: 'https://app.adamas.tech',
    emailOnFailure: true
  })

  const [saving, setSaving] = useState(false)

  const handleProfileSave = async () => {
    setSaving(true)
    // Simulate API delay
    await new Promise(r => setTimeout(r, 600))
    setSaving(false)
    toast.success('Company profile updated successfully!')
  }

  const handleApiSave = async () => {
    setSaving(true)
    await new Promise(r => setTimeout(r, 400))
    setSaving(false)
    toast.success('API configuration saved.')
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[#1a2340]">Settings</h1>
        <p className="text-sm text-[#5a6a85] mt-1">Configure tenant properties and notifications</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6">
          <h2 className="text-lg font-semibold text-[#1a2340] mb-4">Company Profile</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-[#5a6a85] mb-1">Company Name</label>
              <input 
                type="text" 
                value={profile.companyName} 
                onChange={e => setProfile({...profile, companyName: e.target.value})}
                className="w-full border border-[#e3eaf7] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#1a6fcf] focus:ring-1 focus:ring-[#1a6fcf]" 
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-[#5a6a85] mb-1">Tax Registration Number (TRN)</label>
              <input 
                type="text" 
                value={profile.trn} 
                onChange={e => setProfile({...profile, trn: e.target.value})}
                className="w-full border border-[#e3eaf7] rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:border-[#1a6fcf] focus:ring-1 focus:ring-[#1a6fcf]" 
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-[#5a6a85] mb-1">Registered Address</label>
              <textarea 
                rows={3} 
                value={profile.address} 
                onChange={e => setProfile({...profile, address: e.target.value})}
                className="w-full border border-[#e3eaf7] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#1a6fcf] focus:ring-1 focus:ring-[#1a6fcf]"
              />
            </div>
            <div className="pt-2">
              <Button onClick={handleProfileSave} disabled={saving}>{saving ? 'Saving...' : 'Save changes'}</Button>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <h2 className="text-lg font-semibold text-[#1a2340] mb-4">API Configuration</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-[#5a6a85] mb-1">Allowed Origins (CORS)</label>
              <input 
                type="text" 
                value={apiConfig.cors} 
                onChange={e => setApiConfig({...apiConfig, cors: e.target.value})}
                className="w-full border border-[#e3eaf7] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#1a6fcf] focus:ring-1 focus:ring-[#1a6fcf]" 
              />
            </div>
            <div className="pt-2">
              <Button variant="ghost" onClick={handleApiSave}>Update CORS</Button>
            </div>
            
            <div className="pt-4 border-t border-[#e3eaf7]">
              <h3 className="text-sm font-semibold text-[#1a2340] mb-2">Notification Rules</h3>
              <label className="flex items-center gap-2 text-sm text-[#5a6a85] cursor-pointer">
                <input 
                  type="checkbox" 
                  checked={apiConfig.emailOnFailure} 
                  onChange={e => {
                    setApiConfig({...apiConfig, emailOnFailure: e.target.checked})
                    toast.success(e.target.checked ? "Alerts enabled" : "Alerts disabled")
                  }}
                  className="rounded border-[#e3eaf7] text-[#1a6fcf] focus:ring-[#1a6fcf] w-4 h-4 cursor-pointer" 
                />
                Email on validation failure
              </label>
            </div>

            <div className="pt-4 border-t border-[#e3eaf7]">
              <h3 className="text-sm font-semibold text-[#1a2340] mb-2">System</h3>
              <div className="flex justify-between items-center text-sm">
                <span className="text-[#5a6a85]">Rate limit tier</span>
                <span className="font-semibold text-[#1a2340]">Enterprise (500 req/min)</span>
              </div>
              <div className="flex justify-between items-center text-sm mt-2">
                <span className="text-[#5a6a85]">Audit log retention</span>
                <span className="font-semibold text-[#1a2340]">7 Years</span>
              </div>
              <div className="mt-4">
                <Button variant="ghost" onClick={() => toast("Upgrade feature not available in demo", { icon: "ℹ️" })}>Manage Subscription</Button>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}
