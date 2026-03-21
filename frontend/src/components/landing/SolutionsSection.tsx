import { useScrollReveal } from "@/hooks/useScrollReveal";
import { useLanguage } from "@/contexts/LanguageContext";
import { ArrowUpRight } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { TranslationKey } from "@/i18n/translations";

const solutionKeys: { num: string; titleKey: TranslationKey; descKey: TranslationKey; tagKey: TranslationKey }[] = [
  { num: "01", titleKey: "solutions.s1.title", descKey: "solutions.s1.desc", tagKey: "solutions.s1.tag" },
  { num: "02", titleKey: "solutions.s2.title", descKey: "solutions.s2.desc", tagKey: "solutions.s2.tag" },
  { num: "03", titleKey: "solutions.s3.title", descKey: "solutions.s3.desc", tagKey: "solutions.s3.tag" },
  { num: "04", titleKey: "solutions.s4.title", descKey: "solutions.s4.desc", tagKey: "solutions.s4.tag" },
];

export default function SolutionsSection() {
  const headerRef = useScrollReveal<HTMLDivElement>();
  const { t } = useLanguage();

  return (
    <section id="solutions" className="relative py-24 md:py-32">
      <div className="container max-w-5xl mx-auto px-4">
        <div ref={headerRef} className="reveal-up mb-16">
          <span className="text-primary text-xs font-medium uppercase tracking-widest">{t("solutions.tag")}</span>
          <h2 className="font-display text-3xl md:text-5xl font-bold mt-3" style={{ textWrap: "balance" }}>
            {t("solutions.title1")}
            <br />
            <span className="text-gradient-vetc">{t("solutions.title2")}</span>
          </h2>
        </div>

        <div className="flex flex-col gap-4">
          {solutionKeys.map((s, i) => (
            <SolutionRow key={s.num} num={s.num} title={t(s.titleKey)} desc={t(s.descKey)} tag={t(s.tagKey)} index={i} />
          ))}
        </div>

        <div className="mt-12 text-center">
          <Button asChild variant="outline" className="active:scale-95 transition-transform border-border/50 hover:border-primary/30 hover:bg-primary/5">
            <Link to="/core-services">
              {t("solutions.viewAll")}
              <ArrowUpRight className="ml-1 w-4 h-4" />
            </Link>
          </Button>
        </div>
      </div>
    </section>
  );
}

function SolutionRow({ num, title, desc, tag, index }: { num: string; title: string; desc: string; tag: string; index: number }) {
  const ref = useScrollReveal<HTMLDivElement>();
  return (
    <div
      ref={ref}
      className="reveal-left group flex flex-col md:flex-row md:items-center gap-4 md:gap-8 p-6 md:p-8 rounded-2xl border border-border/30 bg-card/30 hover:border-primary/20 hover:bg-card/60 transition-all duration-500 cursor-pointer active:scale-[0.98]"
      style={{ transitionDelay: `${index * 100}ms` }}
    >
      <span className="font-display text-3xl font-bold text-primary/30 group-hover:text-primary/60 transition-colors duration-300 shrink-0 w-16">
        {num}
      </span>
      <div className="flex-1">
        <div className="flex items-center gap-3 mb-1.5">
          <h3 className="font-display font-semibold text-lg text-foreground group-hover:text-primary transition-colors duration-300">
            {title}
          </h3>
          <span className="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full border border-primary/20 text-primary/70 font-medium">
            {tag}
          </span>
        </div>
        <p className="text-muted-foreground text-sm leading-relaxed max-w-xl">{desc}</p>
      </div>
      <ArrowUpRight className="w-5 h-5 text-muted-foreground group-hover:text-primary group-hover:translate-x-1 group-hover:-translate-y-1 transition-all duration-300 shrink-0" />
    </div>
  );
}
