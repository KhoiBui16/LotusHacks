import { useScrollReveal } from "@/hooks/useScrollReveal";
import { useLanguage } from "@/contexts/LanguageContext";
import { Radio, CreditCard, BarChart3, ShieldCheck, Smartphone, Network } from "lucide-react";
import { TranslationKey } from "@/i18n/translations";

const featureKeys: { icon: typeof Radio; titleKey: TranslationKey; descKey: TranslationKey }[] = [
  { icon: Radio, titleKey: "features.rfid.title", descKey: "features.rfid.desc" },
  { icon: CreditCard, titleKey: "features.payment.title", descKey: "features.payment.desc" },
  { icon: BarChart3, titleKey: "features.analytics.title", descKey: "features.analytics.desc" },
  { icon: ShieldCheck, titleKey: "features.security.title", descKey: "features.security.desc" },
  { icon: Smartphone, titleKey: "features.mobile.title", descKey: "features.mobile.desc" },
  { icon: Network, titleKey: "features.network.title", descKey: "features.network.desc" },
];

export default function FeaturesSection() {
  const { t } = useLanguage();
  return (
    <section id="features" className="relative py-24 md:py-32">
      <div className="absolute inset-0 vetc-glow-bottom pointer-events-none" />
      <div className="container max-w-6xl mx-auto px-4 relative z-10">
        <SectionHeader />
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
          {featureKeys.map((f, i) => (
            <FeatureCard key={f.titleKey} icon={f.icon} title={t(f.titleKey)} desc={t(f.descKey)} index={i} />
          ))}
        </div>
      </div>
    </section>
  );
}

function SectionHeader() {
  const ref = useScrollReveal<HTMLDivElement>();
  const { t } = useLanguage();
  return (
    <div ref={ref} className="reveal-up text-center mb-16">
      <span className="text-primary text-xs font-medium uppercase tracking-widest">{t("features.tag")}</span>
      <h2 className="font-display text-3xl md:text-5xl font-bold mt-3 mb-4" style={{ textWrap: "balance" }}>
        {t("features.title1")}<br />
        <span className="text-gradient-vetc">{t("features.title2")}</span>
      </h2>
      <p className="text-muted-foreground max-w-lg mx-auto text-sm md:text-base" style={{ textWrap: "pretty" }}>
        {t("features.subtitle")}
      </p>
    </div>
  );
}

function FeatureCard({ icon: Icon, title, desc, index }: { icon: typeof Radio; title: string; desc: string; index: number }) {
  const ref = useScrollReveal<HTMLDivElement>();
  return (
    <div
      ref={ref}
      className="reveal-3d group relative rounded-2xl border border-border/50 bg-card/50 backdrop-blur-sm p-7 hover:border-primary/20 hover:bg-card/80 transition-all duration-500 hover:shadow-lg hover:shadow-primary/5 active:scale-[0.98]"
      style={{ transitionDelay: `${index * 80}ms` }}
    >
      <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center mb-5 group-hover:bg-primary/15 transition-colors duration-300">
        <Icon className="w-5 h-5 text-primary" />
      </div>
      <h3 className="font-display font-semibold text-foreground mb-2 text-base">{title}</h3>
      <p className="text-muted-foreground text-sm leading-relaxed">{desc}</p>
    </div>
  );
}
