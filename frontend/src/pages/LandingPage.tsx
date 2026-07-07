import Navbar from "../components/landing/Navbar";
import Hero from "../components/landing/Hero";
import DiscoverSection from "../components/landing/DiscoverSection";
import FeatureCards from "../components/landing/FeatureCards";

function LandingPage() {
  return (
    <div className="relative min-h-screen overflow-x-hidden bg-[#FAFAFA] text-gray-900">
      <Navbar />
      <Hero />
      <DiscoverSection />
      <FeatureCards />
    </div>
  );
}

export default LandingPage;
