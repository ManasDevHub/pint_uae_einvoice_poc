import { useEffect, useState } from 'react'
import { API_BASE } from '../constants/api'
import { Activity, Moon, Sun, Zap } from 'lucide-react'

export default function Header({ darkMode, onToggleDark }) {
  const [health, setHealth] = useState('checking')  // checking | online | offline

  useEffect(() => {
    const check = async () => {
      setHealth('checking')
      try {
        const r = await fetch(`${API_BASE}/health/live`, { signal: AbortSignal.timeout(3000) })
        setHealth(r.ok ? 'online' : 'offline')
      } catch {
        setHealth('offline')
      }
    }
    check()
    const t = setInterval(check, 15000)
    return () => clearInterval(t)
  }, [])

  const healthLabel = { checking: 'Checking...', online: 'API online', offline: 'API offline' }

  return (
    <header className="border-b border-[#e3eaf7] bg-[#f8faff]/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="max-w-screen-2xl mx-auto px-6 h-14 flex items-center justify-between">

        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded-md bg-sky-500 flex items-center justify-center">
            <Zap size={14} className="text-[#1a2340]" />
          </div>
          <div>
            <span className="font-semibold text-sm text-[#1a2340]">UAE PINT AE</span>
            <span className="text-[#5a6a85] text-sm ml-2">E-Invoice Engine</span>
          </div>
        </div>

        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <span className={`pulse-dot ${health}`} />
            <span className={`text-xs font-medium ${
              health === 'online' ? 'text-emerald-400'
              : health === 'offline' ? 'text-red-400'
              : 'text-amber-400'
            }`}>{healthLabel[health]}</span>
          </div>

          <button
            onClick={onToggleDark}
            className="p-1.5 rounded-md text-[#8899b0] hover:text-slate-200 hover:bg-[#f8faff] transition-colors"
            title="Toggle theme"
          >
            {darkMode ? <Sun size={16} /> : <Moon size={16} />}
          </button>
        </div>

      </div>
    </header>
  )
}
