import Navbar from "@/components/landing/Navbar";
import Footer from "@/components/landing/Footer";
import { useScrollReveal } from "@/hooks/useScrollReveal";
import { useLanguage } from "@/contexts/LanguageContext";
import { ArrowRight, Radio, Shield, Cpu, BarChart3, Globe } from "lucide-react";
import { Button } from "@/components/ui/button";
import { TranslationKey } from "@/i18n/translations";

const pillars: { id: string; icon: typeof Radio; num: string; titleKey: TranslationKey; subtitleKey: TranslationKey; statValueKey: string; statLabelKey: TranslationKey; description: string; features: string[] }[] = [
  { id: "rfid", icon: Radio, num: "01", titleKey: "cs.p1.title", subtitleKey: "cs.p1.subtitle", statValueKey: "4.2M+", statLabelKey: "cs.p1.stat", description: "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse varius enim in eros elementum tristique.", features: ["Ultra-high frequency passive RFID tags with 10+ year lifespan", "Tamper-proof mounting with vehicle identification binding", "Multi-lane detection at speeds exceeding 120 km/h", "Batch provisioning and remote firmware updates"] },
  { id: "security", icon: Shield, num: "02", titleKey: "cs.p2.title", subtitleKey: "cs.p2.subtitle", statValueKey: "99.99%", statLabelKey: "cs.p2.stat", description: "Praesent commodo cursus magna, vel scelerisque nisl consectetur et.", features: ["End-to-end AES-256 encryption for all transactions", "PCI-DSS Level 1 compliant payment processing", "Real-time fraud detection with ML anomaly scoring", "SOC 2 Type II certified infrastructure"] },
  { id: "processing", icon: Cpu, num: "03", titleKey: "cs.p3.title", subtitleKey: "cs.p3.subtitle", statValueKey: "<200ms", statLabelKey: "cs.p3.stat", description: "Cras mattis consectetur purus sit amet fermentum.", features: ["Sub-200ms transaction processing latency", "Offline-capable edge nodes with automatic sync", "Load-balanced across 82 toll station clusters", "Auto-scaling during peak traffic hours"] },
  { id: "analytics", icon: BarChart3, num: "04", titleKey: "cs.p4.title", subtitleKey: "cs.p4.subtitle", statValueKey: "12B+", statLabelKey: "cs.p4.stat", description: "Nullam id dolor id nibh ultricies vehicula ut id elit.", features: ["Real-time traffic flow visualization dashboards", "Predictive congestion modeling with 94% accuracy", "Revenue forecasting and toll optimization reports", "Custom API endpoints for government data partners"] },
  { id: "integration", icon: Globe, num: "05", titleKey: "cs.p5.title", subtitleKey: "cs.p5.subtitle", statValueKey: "47", statLabelKey: "cs.p5.stat", description: "Maecenas sed diam eget risus varius blandit sit amet non magna.", features: ["RESTful APIs with comprehensive documentation", "Webhook-driven event system for real-time notifications", "Partner SDK for parking, fleet, and smart city platforms", "Interoperable with ASEAN e-toll standards"] },
];

export default function CoreServices() {
  const heroRef = useScrollReveal<HTMLDivElement>(0.1);
  const { t } = useLanguage();

  return (
    <div className="min-h-screen bg-background overflow-x-hidden">
      <Navbar />
      <section className="relative pt-32 pb-20 overflow-hidden">
        <div className="absolute inset-0 vetc-glow pointer-events-none" />
        <div className="container max-w-4xl mx-auto px-4 text-center">
          <div ref={heroRef} className="reveal-up">
            <span className="text-primary text-xs font-medium uppercase tracking-widest">{t("cs.tag")}</span>
            <h1 className="font-display text-4xl sm:text-5xl md:text-6xl font-bold mt-4 mb-6 leading-[0.95]" style={{ textWrap: "balance" }}>
              {t("cs.title1")}<br /><span className="text-gradient-vetc">{t("cs.title2")}</span>
            </h1>
            <p className="text-muted-foreground text-base md:text-lg max-w-2xl mx-auto leading-relaxed" style={{ textWrap: "pretty" }}>{t("cs.subtitle")}</p>
          </div>
        </div>
      </section>

      {pillars.map((pillar, i) => (
        <PillarSection key={pillar.id} pillar={pillar} index={i} />
      ))}

      <section className="py-24 md:py-32">
        <div className="container max-w-3xl mx-auto px-4 text-center"><BottomCTA /></div>
      </section>
      <Footer />
    </div>
  );
}

function PillarSection({ pillar, index }: { pillar: typeof pillars[0]; index: number }) {
  const contentRef = useScrollReveal<HTMLDivElement>(0.15);
  const cardRef = useScrollReveal<HTMLDivElement>(0.15);
  const { t } = useLanguage();
  const isEven = index % 2 === 0;

  return (
    <section id={pillar.id} className={`relative py-20 md:py-28 ${index % 2 === 1 ? "bg-card/30" : ""}`}>
      <div className="container max-w-6xl mx-auto px-4">
        <div className={`flex flex-col ${isEven ? "lg:flex-row" : "lg:flex-row-reverse"} gap-12 lg:gap-20 items-center`}>
          <div ref={contentRef} className="reveal-up flex-1 max-w-xl">
            <div className="flex items-center gap-3 mb-4">
              <span className="font-display text-4xl font-bold text-primary/20">{pillar.num}</span>
              <div className="w-8 h-[1px] bg-primary/30" />
              <span className="text-primary text-xs font-medium uppercase tracking-widest">Pillar {pillar.num}</span>
            </div>
            <h2 className="font-display text-3xl md:text-4xl font-bold mb-2 leading-tight" style={{ textWrap: "balance" }}>{t(pillar.titleKey)}</h2>
            <p className="text-primary/70 text-sm font-medium mb-4">{t(pillar.subtitleKey)}</p>
            <p className="text-muted-foreground text-sm leading-relaxed mb-8" style={{ textWrap: "pretty" }}>{pillar.description}</p>
            <ul className="space-y-3 mb-8">
              {pillar.features.map((f, fi) => (
                <li key={fi} className="flex items-start gap-3 text-sm text-muted-foreground"><span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-primary shrink-0" />{f}</li>
              ))}
            </ul>
            <Button variant="outline" size="sm" className="group active:scale-95 transition-transform border-border/50 hover:border-primary/30 hover:bg-primary/5">
              {t("cs.learnMore")}<ArrowRight className="ml-1 w-3.5 h-3.5 transition-transform duration-200 group-hover:translate-x-1" />
            </Button>
          </div>
          <div ref={cardRef} className="reveal-3d flex-1 max-w-md w-full" style={{ transitionDelay: "150ms" }}>
            <div className="relative rounded-2xl border border-border/30 bg-card/60 p-8 md:p-10 overflow-hidden">
              <div className="absolute -top-20 -right-20 w-40 h-40 rounded-full bg-primary/10 blur-3xl pointer-events-none" />
              <pillar.icon className="w-10 h-10 text-primary mb-6" />
              <div className="flex items-baseline gap-2 mb-1"><span className="font-display text-5xl md:text-6xl font-bold text-foreground tabular-nums">{pillar.statValueKey}</span></div>
              <span className="text-sm text-muted-foreground">{t(pillar.statLabelKey)}</span>
              <div className="absolute bottom-0 left-0 right-0 h-24 opacity-[0.04] pointer-events-none">
                {Array.from({ length: 6 }).map((_, gi) => (<div key={gi} className="absolute left-0 right-0 border-t border-foreground" style={{ bottom: `${gi * 20}%` }} />))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function BottomCTA() {
  const ref = useScrollReveal<HTMLDivElement>(0.2);
  const { t } = useLanguage();
  return (
    <div ref={ref} className="reveal-scale">
      <h2 className="font-display text-3xl md:text-4xl font-bold mb-4" style={{ textWrap: "balance" }}>
        {t("cs.bottomTitle1")}<br /><span className="text-gradient-vetc">{t("cs.bottomTitle2")}</span>?
      </h2>
      <p className="text-muted-foreground text-sm md:text-base max-w-lg mx-auto mb-8 leading-relaxed" style={{ textWrap: "pretty" }}>{t("cs.bottomSubtitle")}</p>
      <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
        <Button size="lg" className="group active:scale-95 transition-transform text-sm px-8">{t("cta.sales")}<ArrowRight className="ml-1 w-4 h-4 transition-transform duration-200 group-hover:translate-x-1" /></Button>
        <Button variant="outline" size="lg" className="active:scale-95 transition-transform text-sm px-8 border-border/50 hover:border-primary/30 hover:bg-primary/5">{t("cta.docs")}</Button>
      </div>
    </div>
  );
}
