import { useState, useEffect } from 'react'
import Card from '../components/ui/Card'
import Pill from '../components/ui/Pill'
import Button from '../components/ui/Button'
import toast from 'react-hot-toast'
import { UserPlus, Save, X, Key, Shield, Clock, CheckCircle2, AlertCircle, Trash2 } from 'lucide-react'
import { API_BASE } from '../constants/api'

const ROLES = ['Admin', 'Analyst', 'Viewer']

export default function Users() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [editingId, setEditingId] = useState(null)
  const [editForm, setEditForm] = useState({})
  const [showAddModal, setShowAddModal] = useState(false)
  const [newUser, setNewUser] = useState({ username: '', email: '', full_name: '', role: 'Analyst', password: '', status: 'Active' })
  const [addingUser, setAddingUser] = useState(false)
  const [auditLog, setAuditLog] = useState([])
  const [activeTab, setActiveTab] = useState('users') // 'users' | 'security'

  useEffect(() => {
    fetchUsers()
    fetchAuditLog()
  }, [])

  const getToken = () => localStorage.getItem('uae_invoice_token')

  const fetchUsers = async () => {
    try {
      setLoading(true)
      const res = await fetch(`${API_BASE}/auth/users`, {
        headers: { 
          'Authorization': `Bearer ${getToken()}`,
        }
      })
      if (!res.ok) throw new Error('Failed to fetch users')
      setUsers(await res.json())
    } catch (e) {
      toast.error(e.message)
    } finally {
      setLoading(false)
    }
  }

  const fetchAuditLog = async () => {
    try {
      const res = await fetch(`${API_BASE}/auth/audit-log?limit=50`, {
        headers: { 
          'Authorization': `Bearer ${getToken()}`,
        }
      })
      if (res.ok) setAuditLog(await res.json())
    } catch (e) {
      // Non-critical, admin only
    }
  }

  const startEdit = (u) => {
    setEditingId(u.id)
    setEditForm({ ...u, password: '' })
  }

  const cancelEdit = () => setEditingId(null)

  const saveEdit = async () => {
    try {
      const body = {
        full_name: editForm.full_name,
        email: editForm.email,
        role: editForm.role,
        status: editForm.status,
      }
      if (editForm.password) body.password = editForm.password

      const res = await fetch(`${API_BASE}/auth/users/${editingId}`, {
        method: 'PATCH',
        headers: { 
          'Authorization': `Bearer ${getToken()}`, 
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body)
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Update failed')
      }
      await fetchUsers()
      setEditingId(null)
      toast.success('User updated successfully')
    } catch (e) {
      toast.error(e.message)
    }
  }

  const handleDelete = async (user) => {
    if (!confirm(`Are you sure you want to delete ${user.full_name}? This action cannot be undone.`)) return
    try {
      const res = await fetch(`${API_BASE}/auth/users/${user.id}`, {
        method: 'DELETE',
        headers: { 
          'Authorization': `Bearer ${getToken()}`,
        }
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Delete failed')
      }
      await fetchUsers()
      toast.success(`User '${user.username}' removed`)
    } catch (e) {
      toast.error(e.message)
    }
  }

  const handleAddUser = async (e) => {
    e.preventDefault()
    if (!newUser.username || !newUser.email || !newUser.full_name || !newUser.password) {
      toast.error('All fields are required')
      return
    }
    try {
      setAddingUser(true)
      const res = await fetch(`${API_BASE}/auth/users`, {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${getToken()}`, 
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newUser)
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Failed to create user')
      }
      await fetchUsers()
      setShowAddModal(false)
      setNewUser({ username: '', email: '', full_name: '', role: 'Analyst', password: '', status: 'Active' })
      toast.success(`User '${newUser.username}' created! They can now sign in.`)
    } catch (e) {
      toast.error(e.message)
    } finally {
      setAddingUser(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-[#1a2340]">User Management</h1>
          <p className="text-sm text-[#5a6a85] mt-1">Create, edit, and manage team access. All changes persist in the database.</p>
        </div>
        <Button variant="primary" onClick={() => setShowAddModal(true)} className="flex items-center gap-2">
          <UserPlus className="w-4 h-4" />
          + Add User
        </Button>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 border-b border-[#e3eaf7]">
        {[
          { key: 'users', label: `Users (${users.length})`, icon: null },
          { key: 'security', label: `Security Log (${auditLog.length})`, icon: Shield },
        ].map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-semibold border-b-2 transition-colors ${
              activeTab === tab.key ? 'border-[#1a6fcf] text-[#1a6fcf]' : 'border-transparent text-[#5a6a85] hover:text-[#1a2340]'
            }`}
          >
            {tab.icon && <tab.icon className="w-3.5 h-3.5" />}
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'users' && (
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="bg-[#f8faff] text-[#5a6a85] border-b border-[#e3eaf7]">
                <tr>
                  <th className="px-6 py-3 font-medium">Name</th>
                  <th className="px-6 py-3 font-medium">Username / Email</th>
                  <th className="px-6 py-3 font-medium">Role</th>
                  <th className="px-6 py-3 font-medium">Status</th>
                  <th className="px-6 py-3 font-medium">Last Login</th>
                  <th className="px-6 py-3 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#e3eaf7]">
                {loading ? (
                  <tr><td colSpan={6} className="px-6 py-10 text-center text-[#8899b0]">Loading users...</td></tr>
                ) : users.map((user) => (
                  <tr key={user.id} className="hover:bg-[#f8faff]">
                    {editingId === user.id ? (
                      <>
                        <td className="px-6 py-3">
                          <input type="text" value={editForm.full_name} onChange={e => setEditForm({...editForm, full_name: e.target.value})}
                            className="w-full border border-[#e3eaf7] rounded px-2 py-1 mb-1.5 text-sm" placeholder="Full Name" />
                          <div className="relative">
                            <Key className="w-3 h-3 absolute left-2 top-1/2 -translate-y-1/2 text-[#8899b0]" />
                            <input type="password" value={editForm.password} onChange={e => setEditForm({...editForm, password: e.target.value})}
                              className="w-full border border-[#e3eaf7] rounded pl-7 py-1 text-xs" placeholder="New password (blank = keep)" />
                          </div>
                        </td>
                        <td className="px-6 py-3"><input type="email" value={editForm.email} onChange={e => setEditForm({...editForm, email: e.target.value})}
                          className="w-full border border-[#e3eaf7] rounded px-2 py-1 text-sm" /></td>
                        <td className="px-6 py-3">
                          <select value={editForm.role} onChange={e => setEditForm({...editForm, role: e.target.value})}
                            className="border border-[#e3eaf7] rounded px-2 py-1 text-sm bg-white">
                            {ROLES.map(r => <option key={r}>{r}</option>)}
                          </select>
                        </td>
                        <td className="px-6 py-3">
                          <select value={editForm.status} onChange={e => setEditForm({...editForm, status: e.target.value})}
                            className="border border-[#e3eaf7] rounded px-2 py-1 text-sm bg-white">
                            <option>Active</option><option>Pending</option>
                          </select>
                        </td>
                        <td className="px-6 py-3 text-[#8899b0] text-xs">—</td>
                        <td className="px-6 py-3 text-right">
                          <div className="flex justify-end gap-2">
                            <button onClick={saveEdit} title="Save" className="text-[#22c55e] hover:bg-[#dcfce7] p-1.5 rounded"><Save className="w-4 h-4" /></button>
                            <button onClick={cancelEdit} title="Cancel" className="text-[#e53e3e] hover:bg-[#fee2e2] p-1.5 rounded"><X className="w-4 h-4" /></button>
                          </div>
                        </td>
                      </>
                    ) : (
                      <>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-full bg-[#1a6fcf]/10 flex items-center justify-center text-xs font-bold text-[#1a6fcf]">
                              {user.avatar || user.full_name?.substring(0,2).toUpperCase()}
                            </div>
                            <span className="font-medium text-[#1a2340]">{user.full_name}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="text-[#1a2340] font-mono text-xs">{user.username}</div>
                          <div className="text-[#8899b0] text-xs">{user.email}</div>
                        </td>
                        <td className="px-6 py-4">
                          <Pill variant={user.role === 'Admin' ? 'violet' : user.role === 'Analyst' ? 'blue' : 'gray'}>{user.role}</Pill>
                        </td>
                        <td className="px-6 py-4">
                          <Pill variant={user.status === 'Active' ? 'green' : 'warning'}>{user.status}</Pill>
                        </td>
                        <td className="px-6 py-4 text-[#8899b0] text-xs">
                          {user.last_login ? new Date(user.last_login).toLocaleString() : 'Never'}
                        </td>
                        <td className="px-6 py-4 text-right">
                          <button onClick={() => startEdit(user)} className="text-[#1a6fcf] hover:underline font-medium text-sm mr-3">Edit</button>
                          <button onClick={() => handleDelete(user)} className="text-[#e53e3e] hover:underline font-medium text-sm">
                            <Trash2 className="w-3.5 h-3.5 inline" />
                          </button>
                        </td>
                      </>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {activeTab === 'security' && (
        <Card className="overflow-hidden">
          <div className="p-4 border-b border-[#e3eaf7] flex items-center gap-3 bg-[#f8faff]">
            <Shield className="w-5 h-5 text-[#1a6fcf]" />
            <div>
              <h2 className="font-semibold text-[#1a2340] text-sm">Security Audit Log</h2>
              <p className="text-xs text-[#5a6a85]">All login attempts, password changes, and system access events</p>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-[#f8faff] text-[#5a6a85] border-b border-[#e3eaf7]">
                <tr>
                  <th className="px-6 py-3 font-medium">User</th>
                  <th className="px-6 py-3 font-medium">Action</th>
                  <th className="px-6 py-3 font-medium">Result</th>
                  <th className="px-6 py-3 font-medium">IP Address</th>
                  <th className="px-6 py-3 font-medium">Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#e3eaf7]">
                {auditLog.length === 0 ? (
                  <tr><td colSpan={5} className="px-6 py-10 text-center text-[#8899b0]">No audit events yet. Events are recorded on login attempts.</td></tr>
                ) : auditLog.map((log) => (
                  <tr key={log.id} className="hover:bg-[#f8faff]">
                    <td className="px-6 py-3 font-mono text-[#1a6fcf] text-sm">{log.username}</td>
                    <td className="px-6 py-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase text-white ${
                        log.action === 'LOGIN' ? 'bg-[#1a6fcf]' :
                        log.action === 'PASSWORD_CHANGE' ? 'bg-[#e07b00]' : 'bg-[#8899b0]'
                      }`}>{log.action}</span>
                    </td>
                    <td className="px-6 py-3">
                      {log.success ? (
                        <span className="flex items-center gap-1 text-[#22c55e] text-xs font-medium">
                          <CheckCircle2 className="w-3.5 h-3.5" /> Success
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 text-[#e53e3e] text-xs font-medium">
                          <AlertCircle className="w-3.5 h-3.5" /> Failed
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-3 text-[#8899b0] font-mono text-xs">{log.ip_address || '—'}</td>
                    <td className="px-6 py-3 text-[#8899b0] text-xs">
                      <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{new Date(log.created_at).toLocaleString()}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* ADD USER MODAL */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#0a0f1e]/60 backdrop-blur-sm">
          <Card className="w-full max-w-lg shadow-2xl">
            <div className="p-5 border-b border-[#e3eaf7] flex items-center justify-between bg-[#f8faff] rounded-t-xl">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-[#1a6fcf]/10 rounded-lg"><UserPlus className="w-5 h-5 text-[#1a6fcf]" /></div>
                <div>
                  <h3 className="font-bold text-[#1a2340]">Create New User</h3>
                  <p className="text-xs text-[#5a6a85]">The new user can sign in immediately after creation</p>
                </div>
              </div>
              <button onClick={() => setShowAddModal(false)} className="p-1.5 hover:bg-[#e3eaf7] rounded-lg">
                <X className="w-5 h-5 text-[#8899b0]" />
              </button>
            </div>

            <form onSubmit={handleAddUser} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-[#5a6a85] uppercase tracking-wider mb-1">Full Name *</label>
                  <input
                    type="text"
                    value={newUser.full_name}
                    onChange={e => setNewUser({...newUser, full_name: e.target.value})}
                    placeholder="John Smith"
                    className="w-full border border-[#e3eaf7] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#1a6fcf]"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-[#5a6a85] uppercase tracking-wider mb-1">Username *</label>
                  <input
                    type="text"
                    value={newUser.username}
                    onChange={e => setNewUser({...newUser, username: e.target.value.toLowerCase().replace(/\s/g, '')})}
                    placeholder="jsmith"
                    className="w-full border border-[#e3eaf7] rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:border-[#1a6fcf]"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#5a6a85] uppercase tracking-wider mb-1">Email *</label>
                <input
                  type="email"
                  value={newUser.email}
                  onChange={e => setNewUser({...newUser, email: e.target.value})}
                  placeholder="john.smith@company.com"
                  className="w-full border border-[#e3eaf7] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#1a6fcf]"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-[#5a6a85] uppercase tracking-wider mb-1">Role *</label>
                  <select
                    value={newUser.role}
                    onChange={e => setNewUser({...newUser, role: e.target.value})}
                    className="w-full border border-[#e3eaf7] rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:border-[#1a6fcf]"
                  >
                    {ROLES.map(r => <option key={r}>{r}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-[#5a6a85] uppercase tracking-wider mb-1">Status</label>
                  <select
                    value={newUser.status}
                    onChange={e => setNewUser({...newUser, status: e.target.value})}
                    className="w-full border border-[#e3eaf7] rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:border-[#1a6fcf]"
                  >
                    <option>Active</option>
                    <option>Pending</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#5a6a85] uppercase tracking-wider mb-1">Initial Password *</label>
                <div className="relative">
                  <Key className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[#8899b0]" />
                  <input
                    type="password"
                    value={newUser.password}
                    onChange={e => setNewUser({...newUser, password: e.target.value})}
                    placeholder="Min 6 characters"
                    className="w-full pl-10 border border-[#e3eaf7] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#1a6fcf]"
                    required
                    minLength={6}
                  />
                </div>
                <p className="text-xs text-[#8899b0] mt-1">The user will use this to sign in. They can change it later.</p>
              </div>

              <div className="flex gap-3 pt-2">
                <Button type="button" variant="ghost" onClick={() => setShowAddModal(false)} className="flex-1">Cancel</Button>
                <Button type="submit" variant="primary" className="flex-1" disabled={addingUser}>
                  {addingUser ? 'Creating...' : 'Create User'}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  )
}
