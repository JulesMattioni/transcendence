import Navbar from "../components/landing/Navbar";
import Hero from "../components/landing/Hero";
import DiscoverSection from "../components/landing/DiscoverSection";
import FeatureCards from "../components/landing/FeatureCards";
import Footer from "../components/landing/Footer";

function LandingPage() {
  return (
    <div className="relative min-h-screen overflow-x-hidden bg-bg text-gray-900">
      <Navbar />
      <Hero />
      <DiscoverSection />
      <FeatureCards />
      <Footer />
    </div>
  );
}

export default LandingPage;
