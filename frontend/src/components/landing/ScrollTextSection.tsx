import { useScrollFillText } from "@/hooks/useScrollReveal";
import { useLanguage } from "@/contexts/LanguageContext";

export default function ScrollTextSection() {
  const textRef = useScrollFillText();
  const { t } = useLanguage();

  return (
    <section id="about" className="relative py-32 md:py-48">
      <div className="container max-w-5xl mx-auto px-4">
        <p
          ref={textRef as React.RefObject<HTMLParagraphElement>}
          className="scroll-fill-text font-display text-2xl sm:text-3xl md:text-5xl font-semibold leading-snug md:leading-tight"
          style={{ textWrap: "balance" }}
        >
          {t("about.text")}
        </p>
      </div>
    </section>
  );
}
