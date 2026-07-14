import type { ReactNode } from 'react'
import Topbar from './Topbar'
import Sidebar from './Sidebar'
import BottomNav from './BottomNav'

function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-screen flex-col overflow-hidden bg-bg">
      {/* Topbar */}
      <Topbar />

      {/* Body */}
      <div className="flex min-h-0 flex-1">
        {/* Sidebar */}
        <Sidebar />

        {/* Content Zone */}
        <main className="pb-24 lg:pb-6 min-h-0 flex-1 overflow-y-auto p-6">{children}</main>
      </div>

      {/* Bottom nav (mobile) */}
      <BottomNav />
    </div>
  )
}

export default DashboardLayout
