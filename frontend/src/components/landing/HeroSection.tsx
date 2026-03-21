import { useScrollReveal } from "@/hooks/useScrollReveal";
import { useLanguage } from "@/contexts/LanguageContext";
import { Button } from "@/components/ui/button";
import { ArrowRight, Shield, Zap, Globe } from "lucide-react";
import { useNavigate } from "react-router-dom";

export default function HeroSection() {
  const titleRef = useScrollReveal<HTMLHeadingElement>(0.1);
  const subRef = useScrollReveal<HTMLParagraphElement>(0.1);
  const ctaRef = useScrollReveal<HTMLDivElement>(0.1);
  const statsRef = useScrollReveal<HTMLDivElement>(0.1);
  const { t } = useLanguage();
  const navigate = useNavigate();

  const scrollToSection = (selector: string) => {
    const el = document.querySelector(selector);
    if (el) {
      el.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden pt-20">
      <div className="absolute inset-0 vetc-glow pointer-events-none" />
      <div className="absolute bottom-0 left-0 right-0 h-64 vetc-glow-bottom pointer-events-none" />
      <div className="absolute top-1/2 left-1/2 w-[900px] h-[900px] rounded-full border border-primary/5 animate-spin-slow pointer-events-none" />
      <div className="absolute top-1/2 left-1/2 w-[700px] h-[700px] rounded-full border border-primary/10 animate-spin-slow-reverse pointer-events-none" />
      <div className="absolute top-1/2 left-1/2 w-[500px] h-[500px] rounded-full border border-primary/15 animate-ring-breathe pointer-events-none" />
      <div className="absolute top-1/2 left-1/2 w-[900px] h-[900px] animate-spin-slow pointer-events-none" style={{ transform: "translate(-50%, -50%)" }}>
        <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 w-2 h-2 rounded-full bg-primary/60 shadow-[0_0_8px_hsl(var(--vetc-glow)/0.6)]" />
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 w-1.5 h-1.5 rounded-full bg-primary/40" />
      </div>
      <div className="absolute top-1/2 left-1/2 w-[700px] h-[700px] animate-spin-slow-reverse pointer-events-none" style={{ transform: "translate(-50%, -50%)" }}>
        <div className="absolute top-1/2 right-0 translate-x-1/2 -translate-y-1/2 w-2 h-2 rounded-full bg-primary/50 shadow-[0_0_8px_hsl(var(--vetc-glow)/0.4)]" />
      </div>

      <div className="container relative z-10 text-center max-w-4xl mx-auto px-4">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-primary/20 bg-primary/5 text-primary text-xs font-medium mb-8 reveal-up revealed">
          <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
          {t("hero.badge")}
        </div>

        <h1
          ref={titleRef}
          className="reveal-up font-display text-4xl sm:text-5xl md:text-7xl font-bold leading-[0.95] mb-6"
          style={{ textWrap: "balance" }}
        >
          {t("hero.title1")}
          <br />
          <span className="text-gradient-vetc">{t("hero.title2")}</span>
          <br />
          {t("hero.title3")}
        </h1>

        <p
          ref={subRef}
          className="reveal-up text-muted-foreground text-base md:text-lg max-w-2xl mx-auto mb-10 leading-relaxed"
          style={{ transitionDelay: "100ms", textWrap: "pretty" }}
        >
          {t("hero.subtitle")}
        </p>

        <div
          ref={ctaRef}
          className="reveal-up flex flex-col sm:flex-row items-center justify-center gap-4"
          style={{ transitionDelay: "200ms" }}
        >
          <Button
            size="lg"
            className="group active:scale-95 transition-transform text-sm px-8"
            onClick={() => scrollToSection("#solutions")}
          >
            {t("hero.cta1")}
            <ArrowRight className="ml-1 w-4 h-4 transition-transform duration-200 group-hover:translate-x-1" />
          </Button>
          <Button
            variant="outline"
            size="lg"
            className="active:scale-95 transition-transform text-sm px-8 border-border/50 hover:border-primary/30 hover:bg-primary/5"
            onClick={() => scrollToSection("#about")}
          >
            {t("hero.cta2")}
          </Button>
        </div>

        <div
          ref={statsRef}
          className="reveal-up grid grid-cols-3 gap-6 mt-20 max-w-lg mx-auto"
          style={{ transitionDelay: "350ms" }}
        >
          {[
            { icon: Zap, value: t("hero.stat1.value"), label: t("hero.stat1.label") },
            { icon: Shield, value: t("hero.stat2.value"), label: t("hero.stat2.label") },
            { icon: Globe, value: t("hero.stat3.value"), label: t("hero.stat3.label") },
          ].map((stat) => (
            <div key={stat.label} className="flex flex-col items-center gap-1.5">
              <stat.icon className="w-4 h-4 text-primary mb-1" />
              <span className="font-display text-xl md:text-2xl font-bold text-foreground tabular-nums">
                {stat.value}
              </span>
              <span className="text-xs text-muted-foreground">{stat.label}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
