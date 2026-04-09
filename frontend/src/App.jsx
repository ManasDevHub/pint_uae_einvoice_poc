import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import { AuthProvider, useAuth } from './context/AuthContext'
import Shell from './components/layout/Shell'
import { Toaster } from 'react-hot-toast'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Validate from './pages/Validate'
import BulkUpload from './pages/BulkUpload'
import History from './pages/History'
import Analytics from './pages/Analytics'
import Integrations from './pages/Integrations'
import Settings from './pages/Settings'
import Users from './pages/Users'
import Reports from './pages/Reports'

function ProtectedRoutes() {
  const { isAuthenticated } = useAuth()
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return (
    <Shell>
      <Toaster position="top-right" toastOptions={{ className: 'text-sm font-medium border border-[#e3eaf7] shadow-sm' }} />
      <Routes>
        <Route path="/dashboard"    element={<Dashboard />} />
        <Route path="/validate"     element={<Validate />} />
        <Route path="/bulk-upload"  element={<BulkUpload />} />
        <Route path="/history"      element={<History />} />
        <Route path="/analytics"    element={<Analytics />} />
        <Route path="/reports"      element={<Reports />} />
        <Route path="/integrations" element={<Integrations />} />
        <Route path="/settings"     element={<Settings />} />
        <Route path="/users"        element={<Users />} />
        <Route path="*"             element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Shell>
  )
}

function AppRoutes() {
  const { isAuthenticated } = useAuth()

  useEffect(() => {
    fetch('/health/live').catch(() => {})
  }, [])

  return (
    <Routes>
      <Route path="/login" element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <Login />} />
      <Route path="/*" element={<ProtectedRoutes />} />
    </Routes>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  )
}
