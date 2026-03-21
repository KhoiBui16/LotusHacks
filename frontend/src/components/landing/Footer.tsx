import { useLanguage } from "@/contexts/LanguageContext";

export default function Footer() {
  const { t } = useLanguage();
  return (
    <footer className="border-t border-border/30 py-12">
      <div className="container max-w-6xl mx-auto px-4">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-md bg-primary flex items-center justify-center font-display font-bold text-primary-foreground text-sm">
              V
            </div>
            <span className="font-display font-semibold text-sm text-foreground">
              {t("footer.brand")}
            </span>
          </div>
          <div className="flex items-center gap-6 text-xs text-muted-foreground">
            <a href="#" className="hover:text-foreground transition-colors">{t("footer.privacy")}</a>
            <a href="#" className="hover:text-foreground transition-colors">{t("footer.terms")}</a>
            <a href="#" className="hover:text-foreground transition-colors">{t("footer.support")}</a>
            <a href="#" className="hover:text-foreground transition-colors">{t("footer.careers")}</a>
          </div>
          <p className="text-xs text-muted-foreground/60">{t("footer.copyright")}</p>
        </div>
      </div>
    </footer>
  );
}
