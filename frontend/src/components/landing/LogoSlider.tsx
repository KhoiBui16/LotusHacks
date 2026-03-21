import { useScrollReveal } from "@/hooks/useScrollReveal";

const partners = [
  "VEC", "VIDIFI", "BOT Trung Luong", "VietinBank", "BIDV",
  "Vietcombank", "MoMo", "ZaloPay", "VNPay", "SHB",
];

export default function LogoSlider() {
  const ref = useScrollReveal<HTMLDivElement>();

  return (
    <section className="py-16 border-y border-border/30">
      <div ref={ref} className="reveal-up">
        <p className="text-center text-xs text-muted-foreground uppercase tracking-widest mb-10">
          Trusted Partners & Integrations
        </p>
        <div className="overflow-hidden relative">
          <div className="absolute left-0 top-0 bottom-0 w-24 bg-gradient-to-r from-background to-transparent z-10 pointer-events-none" />
          <div className="absolute right-0 top-0 bottom-0 w-24 bg-gradient-to-l from-background to-transparent z-10 pointer-events-none" />
          <div className="logo-slider">
            {[...partners, ...partners].map((name, i) => (
              <div
                key={`${name}-${i}`}
                className="shrink-0 mx-8 flex items-center justify-center h-12"
              >
                <span className="font-display text-sm font-semibold text-muted-foreground/40 whitespace-nowrap tracking-wide uppercase hover:text-muted-foreground/70 transition-colors duration-300">
                  {name}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
