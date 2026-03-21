import Navbar from "@/components/landing/Navbar";
import HeroSection from "@/components/landing/HeroSection";
import LogoSlider from "@/components/landing/LogoSlider";
import ScrollTextSection from "@/components/landing/ScrollTextSection";
import FeaturesSection from "@/components/landing/FeaturesSection";
import SolutionsSection from "@/components/landing/SolutionsSection";
import CTASection from "@/components/landing/CTASection";
import Footer from "@/components/landing/Footer";
import ScrollToTopButton from "@/components/landing/ScrollToTopButton";

const Index = () => {
  return (
    <div className="min-h-screen bg-background overflow-x-hidden">
      <Navbar />
      <HeroSection />
      <LogoSlider />
      <ScrollTextSection />
      <FeaturesSection />
      <SolutionsSection />
      <CTASection />
      <Footer />
      <ScrollToTopButton />
    </div>
  );
};

export default Index;
