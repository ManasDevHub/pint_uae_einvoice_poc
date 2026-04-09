import { Bell, LogOut, ChevronDown } from 'lucide-react'
import { useState } from 'react'
import { useAuth } from '../../context/AuthContext'
import { useLocation } from 'react-router-dom'

const PAGE_TITLES = {
  '/dashboard': 'Overview',
  '/validate': 'Validate Invoice',
  '/bulk-upload': 'Bulk Upload',
  '/history': 'Run History',
  '/analytics': 'Analytics',
  '/integrations': 'ERP Integrations',
  '/settings': 'Settings',
  '/users': 'User Management',
}

const ROLE_COLORS = {
  Admin:   { bg: '#7c3aed20', text: '#7c3aed', dot: '#7c3aed' },
  Analyst: { bg: '#1a6fcf20', text: '#1a6fcf', dot: '#1a6fcf' },
  Viewer:  { bg: '#0d7c6620', text: '#0d7c66', dot: '#0d7c66' },
}

export default function Topbar() {
  const { user, logout } = useAuth()
  const location = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)

  const pageTitle = PAGE_TITLES[location.pathname] || 'Overview'
  const roleStyle = ROLE_COLORS[user?.role] || ROLE_COLORS.Viewer

  return (
    <header className="h-16 bg-white border-b border-[#e3eaf7] flex items-center justify-between px-6 shrink-0 z-10 sticky top-0">
      <div className="flex items-center gap-2">
        <img src="/logo.png" alt="Adamas Tech" className="h-8 w-auto object-contain" />
        <span className="text-[#8899b0]">/</span>
        <span className="text-[#1a2340] font-semibold">{pageTitle}</span>
      </div>

      <div className="flex items-center gap-4">
        <div className="bg-[#e8f1ff] text-[#1a6fcf] text-xs font-semibold px-2 py-1 rounded-full">
          PINT AE v1.0
        </div>
        <button className="text-[#5a6a85] hover:text-[#1a6fcf] transition-colors relative">
          <Bell className="w-5 h-5" />
          <span className="absolute top-0 right-0 w-2 h-2 bg-[#e53e3e] rounded-full border border-white" />
        </button>

        {/* User menu */}
        <div className="relative">
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="flex items-center gap-3 pl-4 border-l border-[#e3eaf7] hover:bg-[#f8faff] rounded-lg px-3 py-1.5 transition-colors"
          >
            {/* Avatar */}
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#1a6fcf] to-[#7c3aed] flex items-center justify-center text-white text-xs font-bold shrink-0">
              {user?.avatar || user?.full_name?.[0] || 'U'}
            </div>
            <div className="text-left hidden sm:block">
              <div className="text-sm font-semibold text-[#1a2340] leading-none">{user?.full_name || 'User'}</div>
              <div className="flex items-center gap-1.5 mt-0.5">
                <span
                  className="text-[10px] font-semibold px-1.5 py-0.5 rounded-full"
                  style={{ background: roleStyle.bg, color: roleStyle.text }}
                >
                  {user?.role}
                </span>
              </div>
            </div>
            <ChevronDown className={`w-3.5 h-3.5 text-[#8899b0] transition-transform ${menuOpen ? 'rotate-180' : ''}`} />
          </button>

          {/* Dropdown */}
          {menuOpen && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setMenuOpen(false)} />
              <div className="absolute right-0 top-full mt-2 w-56 bg-white border border-[#e3eaf7] rounded-xl shadow-lg z-20 overflow-hidden">
                <div className="px-4 py-3 bg-[#f8faff] border-b border-[#e3eaf7]">
                  <div className="text-sm font-semibold text-[#1a2340]">{user?.full_name}</div>
                  <div className="text-xs text-[#8899b0] mt-0.5">{user?.email}</div>
                </div>
                <div className="p-2">
                  <button
                    onClick={() => { logout(); setMenuOpen(false) }}
                    className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-[#e53e3e] hover:bg-[#fee2e2] transition-colors font-medium"
                  >
                    <LogOut className="w-4 h-4" />
                    Sign out
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
