import { useScrollReveal } from "@/hooks/useScrollReveal";
import { useLanguage } from "@/contexts/LanguageContext";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { ArrowRight } from "lucide-react";
import { useNavigate } from "react-router-dom";

export default function CTASection() {
  const ref = useScrollReveal<HTMLDivElement>();
  const { t } = useLanguage();
  const { user } = useAuth();
  const navigate = useNavigate();

  const handleDashboardClick = () => {
    if (user) {
      navigate("/dashboard");
    } else {
      navigate("/sign-in");
    }
  };

  return (
    <section id="contact" className="relative py-24 md:py-40">
      <div className="absolute inset-0 vetc-glow pointer-events-none" />
      <div className="container max-w-3xl mx-auto px-4 text-center relative z-10">
        <div ref={ref} className="reveal-scale">
          <h2 className="font-display text-3xl md:text-5xl font-bold mb-5" style={{ textWrap: "balance" }}>
            {t("cta.title1")}
            <br />
            <span className="text-gradient-vetc">{t("cta.title2")}</span>
          </h2>
          <p className="text-muted-foreground mb-10 max-w-md mx-auto text-sm md:text-base" style={{ textWrap: "pretty" }}>
            {t("cta.subtitle")}
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Button size="lg" className="group active:scale-95 transition-transform px-8" onClick={handleDashboardClick}>
              Go to Dashboard
              <ArrowRight className="ml-1 w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
}
