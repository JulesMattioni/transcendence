import { Link } from 'react-router-dom'

/** Landing page top navigation with brand and sign-in / sign-up actions. */
function Navbar() {
  return (
    <nav className="absolute inset-x-0 top-0 z-20 flex items-center justify-between px-6 py-5 sm:px-10">
      {/* Logo */}
      <a
        href="/"
      >
        <span className="font-sans text-2xl font-bold tracking-tight text-gray-900">
            Keepr<span className="text-keepr">.</span>
        </span>
      </a>

      {/* Actions */}
      <div className="flex items-center gap-4 sm:gap-6">
        <Link
          to="/login"
          className="text-sm font-medium text-gray-700 transition-colors hover:text-gray-900"
        >
          Sign In
        </Link>
        <Link
          to="/register"
          className="rounded bg-keepr px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-blue-700"
        >
          Get Started
        </Link>
      </div>
    </nav>
  )
}

export default Navbar
