import { Link, useLocation } from 'react-router-dom'
import { LayoutDashboard, CheckCircle, Upload, History, PieChart, Server, Settings, Users, FileBarChart2 } from 'lucide-react'
import { useHealth } from '../../hooks/useHealth'

export default function Sidebar() {
  const { pathname } = useLocation()
  const { isOnline } = useHealth()

  const navItems = [
    { label: "Dashboard", path: "/dashboard", icon: LayoutDashboard },
    { label: "Validate invoice", path: "/validate", icon: CheckCircle },
    { label: "Bulk upload", path: "/bulk-upload", icon: Upload },
    { label: "Run history", path: "/history", icon: History },
    { label: "Analytics", path: "/analytics", icon: PieChart },
    { label: "Reports", path: "/reports", icon: FileBarChart2 },
  ]

  const sysItems = [
    { label: "ERP integrations", path: "/integrations", icon: Server },
    { label: "Settings", path: "/settings", icon: Settings },
    { label: "User management", path: "/users", icon: Users },
  ]

  return (
    <aside className="w-64 bg-white border-r border-[#e3eaf7] flex flex-col h-full shrink-0">
      <div className="h-16 flex items-center px-6 border-b border-[#e3eaf7]">
        <div className="flex flex-col items-center w-full gap-2">
          <img src="/logo.png" alt="Adamas Tech" className="h-14 w-auto object-contain" />
          <div className="flex flex-col items-center">
            <span className="text-[10px] font-bold text-[#1a6fcf] leading-none uppercase tracking-widest">E-Invoice Engine</span>
            <span className="text-[8px] font-medium text-[#5a6a85] mt-1 tracking-tighter uppercase">UAE PINT AE Compliance</span>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto py-6 px-4 flex flex-col gap-8">
        <div>
          <div className="text-xs font-semibold text-[#8899b0] uppercase tracking-wider mb-3 px-2">Platform</div>
          <div className="flex flex-col gap-1">
            {navItems.map(item => (
              <Link 
                key={item.path} 
                to={item.path}
                className={`flex items-center gap-3 px-2 py-2 rounded-lg text-sm font-medium transition-colors ${
                  pathname.startsWith(item.path) 
                    ? 'bg-[#1a6fcf] text-white' 
                    : 'text-[#5a6a85] hover:bg-[#e8f1ff] hover:text-[#1a6fcf]'
                }`}
              >
                <item.icon className="w-5 h-5" />
                {item.label}
              </Link>
            ))}
          </div>
        </div>

        <div>
          <div className="text-xs font-semibold text-[#8899b0] uppercase tracking-wider mb-3 px-2">System</div>
          <div className="flex flex-col gap-1">
            {sysItems.map(item => (
              <Link 
                key={item.path} 
                to={item.path}
                className={`flex items-center gap-3 px-2 py-2 rounded-lg text-sm font-medium transition-colors ${
                  pathname.startsWith(item.path) 
                    ? 'bg-[#1a6fcf] text-white' 
                    : 'text-[#5a6a85] hover:bg-[#e8f1ff] hover:text-[#1a6fcf]'
                }`}
              >
                <item.icon className="w-5 h-5" />
                {item.label}
              </Link>
            ))}
          </div>
        </div>
      </div>

      <div className="p-4 border-t border-[#e3eaf7]">
        <div className="flex items-center gap-3 px-2">
          <div className={`w-2.5 h-2.5 rounded-full ${isOnline ? 'bg-[#22c55e]' : 'bg-[#e53e3e]'}`} />
          <span className="text-sm font-medium text-[#5a6a85]">
            {isOnline ? 'API online' : 'API offline'}
          </span>
        </div>
      </div>
    </aside>
  )
}
