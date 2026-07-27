import { Link } from "react-router-dom";
import Navbar from "../components/landing/Navbar";
import Footer from "../components/landing/Footer";

/**
 * Fallback page rendered when no route matches the requested URL.
 */
function NotFoundPage() {
  return (
    <div className="relative flex min-h-screen flex-col overflow-x-hidden bg-bg text-gray-900">
      <Navbar />

      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col items-center justify-center px-6 py-28 text-center sm:px-10">
        <span className="inline-flex items-center gap-2 rounded-full border border-gray-300 bg-white px-4 py-1.5 font-mono text-xs text-muted shadow-sm">
          <span className="h-2 w-2 rounded-full bg-keepr" />
          Error 404
        </span>

        <h1 className="mt-6 font-serif text-5xl leading-tight font-bold text-black sm:text-6xl">
          This page <span className="text-keepr">doesn't exist.</span>
        </h1>

        <p className="mt-4 max-w-xl font-sans text-lg font-normal text-muted">
          The page you're looking for may have been moved, renamed, or never
          existed at all.
        </p>

        <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
          <Link
            to="/"
            className="rounded bg-keepr px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-blue-700"
          >
            Back to home
          </Link>
          <Link
            to="/dashboard"
            className="rounded border border-gray-300 bg-white px-6 py-3 text-sm font-semibold text-black transition-colors hover:bg-gray-50"
          >
            Go to dashboard
          </Link>
        </div>
      </main>

      <Footer />
    </div>
  );
}

export default NotFoundPage;
