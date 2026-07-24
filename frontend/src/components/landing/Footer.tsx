import { Link } from "react-router-dom"

/** Landing page footer with brand, legal links and copyright. */
function Footer() {
  return (
    <footer className="bg-keepr px-6 py-12 text-white sm:px-10">
      <div className="flex flex-col items-center gap-6 sm:flex-row sm:justify-between">
        {/* Logo */}
        <a
          href="/"
          className="font-sans text-2xl font-bold tracking-tight text-white"
        >
          Keepr.
        </a>

        {/* Links */}
        <nav className="flex items-center gap-6 text-sm">
          <Link to="/privacy" className="text-white/80 transition-colors hover:text-white">
            Privacy Policy
          </Link>
          <Link to="/terms" className="text-white/80 transition-colors hover:text-white">
            Terms of Service
          </Link>
        </nav>
      </div>

      {/* Copyright */}
      <div className="mt-8 border-t border-white/20 pt-6 text-center text-xs text-white/70">
        © {new Date().getFullYear()} Keepr. All rights reserved.
      </div>
    </footer>
  )
}

export default Footer
