import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { PanelLeft, LogOut } from 'lucide-react'
import { navItems } from './NavItems'

function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <aside
      className={`hidden flex-col border-r border-gray-200 bg-bg transition-all duration-200 lg:flex ${
        collapsed ? 'w-14' : 'w-56'
      }`}
    >
      {/* Collapse button */}
      <button
        type="button"
        onClick={() => setCollapsed((c) => !c)}
        className="flex items-center gap-3 px-4 py-4 text-sm text-muted transition-colors duration-200 hover:bg-blue-100"
      >
        <PanelLeft size={20} className="shrink-0 text-muted" />
        {!collapsed && <span>Close</span>}
      </button>

      {/* Nav Items */}
      <nav className="flex-1">
        {navItems.map((item) => {
          const Icon = item.icon
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 text-sm transition-colors duration-200 ${
                  isActive
                    ? 'bg-keepr text-white'
                    : 'text-muted hover:bg-blue-100'
                }`
              }
            >
              <Icon size={20} className="shrink-0" />
              {!collapsed && <span>{item.label}</span>}
            </NavLink>
          )
        })}
      </nav>

      {/* Logout */}
      <button
        type="button"
        className="flex items-center gap-3 bg-red-50 px-4 py-4 text-sm text-red-500 transition-colors duration-200 hover:bg-red-100"
      >
        <LogOut size={20} className="shrink-0" />
        {!collapsed && <span>Logout</span>}
      </button>
    </aside>
  )
}

export default Sidebar
