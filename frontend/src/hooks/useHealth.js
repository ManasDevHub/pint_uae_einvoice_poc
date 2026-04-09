import { useState, useEffect } from 'react'
import { API_BASE } from '../constants/api'

export function useHealth() {
  const [isOnline, setIsOnline] = useState(true)

  useEffect(() => {
    let mounted = true
    
    async function check() {
      try {
        const res = await fetch(`${API_BASE}/health/live`, {
          headers: { 'ngrok-skip-browser-warning': 'true' }
        })
        if (mounted) setIsOnline(res.ok)
      } catch (e) {
        if (mounted) setIsOnline(false)
      }
    }

    check()
    const interval = setInterval(check, 10000)
    
    return () => {
      mounted = false
      clearInterval(interval)
    }
  }, [])

  return { isOnline }
}
