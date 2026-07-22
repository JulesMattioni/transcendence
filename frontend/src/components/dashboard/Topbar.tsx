import { useEffect, useState } from "react";
import { Bell, User, ChevronDown } from "lucide-react";
import { Link } from "react-router-dom";
import { me } from "../../api/auth";
import { getAvatarUrl } from "../../utils/avatars";
import { useOrg } from "../../context/orgContextValue";

function Topbar() {
  const [avatarId, setAvatarId] = useState<number | null>(null);
  const { orgs, currentOrg, loading, setCurrentOrg } = useOrg();

  useEffect(() => {
    let active = true;
    me()
      .then((data) => active && setAvatarId(data.avatar_id))
      .catch(() => {
      });
    return () => {
      active = false;
    };
  }, [])
  return (
    <header className="flex h-16 items-center justify-between border-b border-gray-200 px-6">
      {/* Logo */}
      <span className="font-sans text-xl font-bold text-black">
        Keepr<span className="text-keepr">.</span>
      </span>

      {/* Org selector */}
      <div className="relative">
        {loading ? (
          <span className="px-4 text-sm text-muted">Loading…</span>
        ) : orgs.length === 0 ? (
          <span className="px-4 text-sm text-muted">No organisation yet</span>
        ) : (
          <>
            <select
              value={currentOrg?.org_id ?? ""}
              onChange={(e) => setCurrentOrg(Number(e.target.value))}
              className="appearance-none py-2 pr-9 pl-4 text-sm text-black focus:outline-none"
            >
              {orgs.map((org) => (
                <option key={org.org_id} value={org.org_id}>
                  {org.name}
                </option>
              ))}
            </select>
            <ChevronDown
              size={16}
              className="pointer-events-none absolute top-1/2 right-3 -translate-y-1/2 text-gray-700"
            />
          </>
        )}
      </div>


      {/* Profile */}
      <div className="flex items-center gap-4">
        <button
          type="button"
          className="text-keepr transition-colors duration-200 hover:text-blue-700"
        >
          <Bell size={22} fill="currentColor" />
        </button>
        <Link
          to="/dashboard/user"
          className="flex h-8 w-8 items-center justify-center overflow-hidden rounded-full bg-keepr text-white"
        >
          {avatarId !== null ? (
            <img
              src={getAvatarUrl(avatarId)}
              alt="Profile"
              className="h-full w-full object-cover"
            />
          ) : (
            <User size={18} />
          )}
        </Link>

      </div>
    </header>
  );
}

export default Topbar;
