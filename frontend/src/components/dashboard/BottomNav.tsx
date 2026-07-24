import { NavLink, useNavigate } from "react-router-dom";
import { LogOut } from "lucide-react";
import { navItems } from "./NavItems";
import { useOrg } from "../../context/orgContextValue";
import { logout } from "../../api/auth";

function BottomNav() {
  const { isAdmin } = useOrg();
  const navigate = useNavigate();
  const visibleItems = navItems.filter((item) => !item.adminOnly || isAdmin);

  async function handleLogout() {
    try {
      await logout();
    } finally {
      navigate("/");
    }
  }

  return (
    <div className="fixed inset-x-0 bottom-0 z-40 flex items-center justify-around py-4 lg:hidden">
      <nav className="flex items-center justify-around border border-gray-200 bg-white lg:hidden">
        {visibleItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end
              className={({ isActive }) =>
                `flex flex-col items-center gap-1 px-4 py-2 text-xs transition-colors ${
                  isActive
                    ? "bg-keepr text-white"
                    : "text-muted hover:bg-gray-50"
                }`
              }
            >
              <Icon size={20} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
        <button
          type="button"
          onClick={handleLogout}
          className="flex flex-col items-center gap-1 px-4 py-2 text-xs text-red-500 transition-colors hover:bg-red-50"
        >
          <LogOut size={20} />
          <span>Logout</span>
        </button>
      </nav>
    </div>
  );
}

export default BottomNav;
