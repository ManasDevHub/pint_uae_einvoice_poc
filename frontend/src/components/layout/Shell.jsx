import Sidebar from './Sidebar'
import Topbar from './Topbar'

export default function Shell({ children }) {
  return (
    <div className="flex h-screen bg-[#f0f4fb] overflow-hidden">
      <Sidebar />
      <div className="flex flex-col flex-1 overflow-hidden">
        <Topbar />
        <main className="flex-1 overflow-y-auto p-8">
          {children}
        </main>
      </div>
    </div>
  )
}
