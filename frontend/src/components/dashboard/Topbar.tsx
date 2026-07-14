import { Bell, User, ChevronDown } from "lucide-react";

function Topbar() {
  return (
    <header className="flex h-16 items-center justify-between border-b border-gray-200 px-6">
      {/* Logo */}
      <span className="font-sans text-xl font-bold text-black">
        Keepr<span className="text-keepr">.</span>
      </span>

      {/* Org selector */}
      <div className="relative">
        <select className="appearance-none py-2 pr-9 pl-4 text-sm text-black focus:outline-none">
          <option>My Organisation</option>
          <option>Another Org</option>
        </select>
        <ChevronDown
          size={16}
          className="pointer-events-none absolute top-1/2 right-3 -translate-y-1/2 text-gray-700"
        />
      </div>

      {/* Profile */}
      <div className="flex items-center gap-4">
        <button
          type="button"
          className="text-keepr transition-colors duration-200 hover:text-blue-700"
        >
          <Bell size={22} fill="currentColor" />
        </button>
        <button
          type="button"
          className="flex h-8 w-8 items-center justify-center rounded-full bg-keepr text-white"
        >
          <User size={18} />
        </button>
      </div>
    </header>
  );
}

export default Topbar;
