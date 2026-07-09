import type { ReactNode } from 'react'
import Topbar from './Topbar'
import Sidebar from './Sidebar'
import BottomNav from './BottomNav'

function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col bg-bg">
      {/* Topbar */}
      <Topbar/>

      {/* Body */}
      <div className="flex flex-1">
        {/* Sidebar (desktop) */}
        <Sidebar/>

        {/* Content Zone */}
        <main className="flex-1 p-6">{children}</main>
      </div>

      {/* Bottom nav (mobile) */}
      <BottomNav/>
    </div>
  )
}

export default DashboardLayout
