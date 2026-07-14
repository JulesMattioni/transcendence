import { NavLink } from 'react-router-dom'
import { navItems } from './NavItems'

function BottomNav() {
  return (
    <div className="fixed inset-x-0 bottom-0 z-40 flex items-center justify-around py-4 lg:hidden">
      <nav className="flex items-center justify-around border border-gray-200 bg-white lg:hidden">
        {navItems.map((item) => {
          const Icon = item.icon
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end
              className={({ isActive }) =>
                `flex flex-col items-center gap-1 px-4 py-2 text-xs transition-colors ${
                  isActive ? 'bg-keepr text-white' : 'text-muted hover:bg-gray-50'
                }`
              }
            >
              <Icon size={20} />
              <span>{item.label}</span>
            </NavLink>
          )
        })}
      </nav>
    </div>
  )
}


export default BottomNav
