import { Link } from "react-router-dom";
import Navbar from "../components/landing/Navbar";
import Footer from "../components/landing/Footer";

interface LegalPageProps {
  title: string;
  lastUpdated: string;
  children: React.ReactNode;
}

/**
 * Shared layout for legal pages (privacy, terms): navbar, a titled header
 * with a last-updated line, the page content, and the footer.
 */
function LegalPage({ title, lastUpdated, children }: LegalPageProps) {
  return (
    <div className="relative min-h-screen overflow-x-hidden bg-bg text-gray-900">
      <Navbar />

      <main className="mx-auto max-w-3xl px-6 pb-20 pt-28 sm:px-10 sm:pt-32">
        <Link
          to="/"
          className="mb-8 inline-flex items-center gap-1 text-sm font-medium text-gray-500 transition-colors hover:text-gray-900"
        >
          ← Back to home
        </Link>

        <h1 className="font-sans text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
          {title}
        </h1>
        <p className="mt-2 text-sm text-gray-500">Last updated: {lastUpdated}</p>

        <div className="legal-content mt-10 space-y-8 text-[15px] leading-relaxed text-gray-700">
          {children}
        </div>
      </main>

      <Footer />
    </div>
  );
}

export default LegalPage;
