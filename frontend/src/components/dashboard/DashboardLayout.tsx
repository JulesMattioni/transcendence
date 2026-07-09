import type { ReactNode } from 'react'
import Topbar from './Topbar'
import Sidebar from './Sidebar'

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
      <nav className="border-t border-gray-200 p-4 text-center text-sm text-muted lg:hidden">
        [ bottom nav mobile ]
      </nav>
    </div>
  )
}

export default DashboardLayout
