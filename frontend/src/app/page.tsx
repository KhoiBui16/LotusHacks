"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Image from "next/image";

import heroGraphic from "../../images/cw1rxDPqCrU.png";
import portrait from "../../images/portrait.png";

import menuIcon from "../../images/icons/hugeicons-menu-01.svg";
import arrowRightIcon from "../../images/icons/solar-arrow-right-linear.svg";
import walletIcon from "../../images/icons/solar-wallet-money-bold.svg";
import routingIcon from "../../images/icons/solar-routing-2-bold.svg";
import shieldIcon from "../../images/icons/solar-shield-check-bold.svg";
import billIcon from "../../images/icons/solar-bill-list-bold.svg";
import cardIcon from "../../images/icons/solar-card-2-bold.svg";
import phoneIcon from "../../images/icons/solar-phone-bold.svg";
import letterIcon from "../../images/icons/solar-letter-bold.svg";
import mapIcon from "../../images/icons/solar-map-point-bold.svg";
import historyIcon from "../../images/icons/solar-history-bold.svg";
import checkReadIcon from "../../images/icons/solar-check-read-bold.svg";
import playIcon from "../../images/icons/solar-play-circle-bold.svg";
import facebookIcon from "../../images/icons/mdi-facebook.svg";
import linkedinIcon from "../../images/icons/mdi-linkedin.svg";
import youtubeIcon from "../../images/icons/mdi-youtube.svg";

type AssetLike = { src: string } | string;

function assetSrc(asset: AssetLike): string {
  return typeof asset === "string" ? asset : asset.src;
}

function Icon({
  src,
  alt,
  className,
}: {
  src: AssetLike;
  alt: string;
  className?: string;
}) {
  return (
    <img
      src={assetSrc(src)}
      alt={alt}
      className={`icon-tint ${className ?? ""}`}
      loading="lazy"
    />
  );
}

function clamp01(value: number) {
  return Math.min(1, Math.max(0, value));
}

function useScrollFill() {
  useEffect(() => {
    let raf = 0;

    const update = () => {
      const nodes = document.querySelectorAll<HTMLElement>("[data-fill]");
      const vh = window.innerHeight || 1;

      nodes.forEach((el) => {
        const rect = el.getBoundingClientRect();
        const total = vh + rect.height;
        const progress = clamp01((vh - rect.top) / total);
        el.style.setProperty("--fill", `${Math.round(progress * 100)}%`);
      });
    };

    const onScroll = () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(update);
    };

    update();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
    };
  }, []);
}

function useInView<T extends Element>(threshold = 0.2) {
  const ref = useRef<T | null>(null);
  const [inView, setInView] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const io = new IntersectionObserver(
      (entries) => {
        const entry = entries[0];
        setInView(entry?.isIntersecting ?? false);
      },
      { threshold }
    );

    io.observe(el);
    return () => io.disconnect();
  }, [threshold]);

  return { ref, inView };
}

function useSectionProgress<T extends Element>() {
  const ref = useRef<T | null>(null);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    let raf = 0;

    const update = () => {
      const el = ref.current;
      if (!el) return;
      const rect = el.getBoundingClientRect();
      const vh = window.innerHeight || 1;
      const total = vh + rect.height;
      const p = clamp01((vh - rect.top) / total);
      setProgress(p);
    };

    const onScroll = () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(update);
    };

    update();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
    };
  }, []);

  return { ref, progress };
}

function ScrollFillHeading({
  eyebrow,
  title,
  subtitle,
}: {
  eyebrow: string;
  title: string;
  subtitle?: string;
}) {
  return (
    <div className="mx-auto max-w-5xl px-6">
      <div className="flex items-center gap-3 text-sm text-emerald-100/70">
        <span className="h-[1px] w-10 bg-emerald-200/20" />
        <span className="tracking-[0.24em] uppercase">{eyebrow}</span>
      </div>
      <h2
        data-fill
        className="text-fill mt-4 text-4xl font-semibold leading-tight md:text-6xl"
      >
        {title}
      </h2>
      {subtitle ? (
        <p className="mt-5 max-w-2xl text-lg text-emerald-50/70">{subtitle}</p>
      ) : null}
    </div>
  );
}

function LoopMarquee({ items }: { items: string[] }) {
  const doubled = useMemo(() => [...items, ...items], [items]);

  return (
    <div className="mx-auto mt-10 max-w-6xl overflow-hidden px-6">
      <div className="relative rounded-2xl border border-emerald-200/10 bg-emerald-950/40 py-4">
        <div className="pointer-events-none absolute inset-0 rounded-2xl [mask-image:linear-gradient(to_right,transparent,black_12%,black_88%,transparent)]" />
        <div className="marquee flex w-[200%] gap-3 px-6">
          {doubled.map((label, idx) => (
            <div
              key={`${label}-${idx}`}
              className="whitespace-nowrap rounded-full border border-emerald-200/10 bg-emerald-950/60 px-4 py-2 text-sm text-emerald-50/70"
            >
              {label}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function ThreeDShowcase() {
  const { ref, progress } = useSectionProgress<HTMLDivElement>();
  const { ref: viewRef, inView } = useInView<HTMLDivElement>(0.35);
  const [active, setActive] = useState(0);

  const slides = useMemo(
    () => [
      {
        title: "Automatic Toll Collection",
        desc: "Fast, cashless passes with transparent, auditable transactions.",
      },
      {
        title: "VETC E-Wallet Experiences",
        desc: "Unified payments, top-ups, and digital services built for daily mobility.",
      },
      {
        title: "Privacy & Data Protection",
        desc: "Design with consent, security, and compliance as first-class features.",
      },
    ],
    []
  );

  useEffect(() => {
    if (!inView) return;
    const id = window.setInterval(() => {
      setActive((v) => (v + 1) % slides.length);
    }, 3200);
    return () => window.clearInterval(id);
  }, [inView, slides.length]);

  const p = progress;
  const tilt = (1 - p) * 18;
  const rise = Math.round(p * 80);
  const glow = Math.round(p * 100);

  return (
    <section ref={viewRef} className="relative py-20 md:py-28">
      <ScrollFillHeading
        eyebrow="Scroll Experience"
        title="3D transitions that reveal what matters"
        subtitle="Scroll down to trigger depth, rotation, and a looping 3D slider inspired by modern AI cloud landing pages."
      />

      <div className="mx-auto mt-12 max-w-6xl px-6">
        <div
          ref={ref}
          className="relative overflow-hidden rounded-3xl border border-emerald-200/10 bg-[linear-gradient(to_bottom,rgba(4,27,18,0.65),rgba(7,42,28,0.45))] p-6 shadow-glow md:p-10"
        >
          <div className="pointer-events-none absolute inset-0 bg-grid-soft [background-size:36px_36px] opacity-[0.22]" />
          <div className="pointer-events-none absolute inset-0 bg-radial-soft opacity-80" />

          <div className="relative grid gap-8 md:grid-cols-2 md:items-center">
            <div>
              <h3 className="text-2xl font-semibold text-emerald-50 md:text-3xl">
                Built for real-world mobility systems
              </h3>
              <p className="mt-4 text-emerald-50/70">
                This concept focuses on speed, trust, and user clarity. The
                interaction highlights key capabilities as you scroll, without
                losing content hierarchy.
              </p>
              <div className="mt-6 grid gap-3 sm:grid-cols-2">
                {[
                  { k: "Hotline", v: "1900 6010" },
                  { k: "HQ", v: "Tasco Building, Hanoi" },
                  { k: "Latency", v: "Low, regional-first" },
                  { k: "Docs", v: "OpenAPI + Swagger UI" },
                ].map((item) => (
                  <div
                    key={item.k}
                    className="rounded-2xl border border-emerald-200/10 bg-emerald-950/50 p-4"
                  >
                    <div className="text-xs tracking-[0.22em] uppercase text-emerald-100/60">
                      {item.k}
                    </div>
                    <div className="mt-2 text-base font-medium text-emerald-50">
                      {item.v}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="relative">
              <div
                className="relative h-[360px] w-full"
                style={{
                  perspective: "1000px",
                }}
              >
                <div
                  className="absolute inset-0"
                  style={{
                    transformStyle: "preserve-3d",
                    transform: `rotateX(${tilt}deg) rotateY(${-tilt * 0.85}deg) translateZ(${rise}px)`,
                    transition: "transform 120ms linear",
                  }}
                >
                  {slides.map((s, idx) => {
                    const delta = (idx - active + slides.length) % slides.length;
                    const order = delta === 0 ? 0 : delta === 1 ? 1 : -1;
                    const z = order === 0 ? 80 : 0;
                    const x = order === 0 ? 0 : order === 1 ? 120 : -120;
                    const rot = order === 0 ? 0 : order === 1 ? 14 : -14;
                    const opacity = order === 0 ? 1 : 0.45;

                    return (
                      <div
                        key={s.title}
                        className="absolute left-1/2 top-1/2 w-[92%] -translate-x-1/2 -translate-y-1/2 rounded-3xl border border-emerald-200/10 bg-emerald-950/70 p-6 backdrop-blur"
                        style={{
                          transform: `translate3d(${x}px, 0, ${z}px) rotateY(${rot}deg)`,
                          opacity,
                          transition:
                            "transform 700ms cubic-bezier(.2,.8,.2,1), opacity 700ms cubic-bezier(.2,.8,.2,1)",
                          boxShadow: `0 0 ${40 + glow}px rgba(47, 208, 138, ${
                            0.12 + p * 0.12
                          })`,
                        }}
                      >
                        <div className="text-xs tracking-[0.22em] uppercase text-emerald-100/60">
                          Slide {idx + 1}
                        </div>
                        <div className="mt-2 text-xl font-semibold text-emerald-50">
                          {s.title}
                        </div>
                        <div className="mt-3 text-sm leading-relaxed text-emerald-50/70">
                          {s.desc}
                        </div>
                        <div className="mt-5 flex items-center gap-3">
                          {slides.map((_, dotIdx) => (
                            <button
                              key={dotIdx}
                              type="button"
                              onClick={() => setActive(dotIdx)}
                              className={`h-2.5 w-2.5 rounded-full transition ${
                                dotIdx === active
                                  ? "bg-vetc-300 shadow-glowStrong"
                                  : "bg-emerald-200/20 hover:bg-emerald-200/35"
                              }`}
                              aria-label={`Go to slide ${dotIdx + 1}`}
                            />
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="mt-5 flex items-center justify-between text-xs text-emerald-100/60">
                <span>Auto-loop while this section is visible</span>
                <span className="tabular-nums">{Math.round(p * 100)}% scroll</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

export default function Home() {
  useScrollFill();

  return (
    <main className="min-h-screen">
      <header className="sticky top-0 z-30 border-b border-emerald-200/10 bg-emerald-950/45 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-vetc-300 to-vetc-600 shadow-glow" />
            <div className="leading-tight">
              <div className="text-sm font-semibold text-emerald-50">
                VETC Technologies
              </div>
              <div className="text-xs text-emerald-100/60">
                Web landing concept
              </div>
            </div>
          </div>

          <nav className="hidden items-center gap-8 text-sm text-emerald-50/70 md:flex">
            <a className="hover:text-emerald-50" href="#capabilities">
              Capabilities
            </a>
            <a className="hover:text-emerald-50" href="#platform">
              Platform
            </a>
            <a className="hover:text-emerald-50" href="#contact">
              Contact
            </a>
          </nav>

          <div className="flex items-center gap-3">
            <button
              type="button"
              className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-emerald-200/10 bg-emerald-950/50 hover:border-emerald-200/20 md:hidden"
              aria-label="Open menu"
            >
              <Icon src={menuIcon} alt="" className="h-5 w-5" />
            </button>
            <a
              href="#contact"
              className="inline-flex items-center gap-2 rounded-full bg-vetc-600 px-4 py-2 text-sm font-semibold text-emerald-950 shadow-glow hover:bg-vetc-500"
            >
              Request a demo
              <Icon src={arrowRightIcon} alt="" className="h-4 w-4" />
            </a>
          </div>
        </div>
      </header>

      <section className="relative overflow-hidden py-16 md:py-24">
        <div className="pointer-events-none absolute inset-0 bg-grid-soft [background-size:44px_44px] opacity-[0.14]" />

        <div className="mx-auto grid max-w-6xl gap-12 px-6 md:grid-cols-2 md:items-center">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-200/10 bg-emerald-950/60 px-4 py-2 text-xs text-emerald-50/70">
              <span className="h-1.5 w-1.5 rounded-full bg-vetc-300 shadow-glow" />
              Built for high-trust mobility payments
            </div>

            <h1 className="mt-6 text-5xl font-semibold leading-tight text-emerald-50 md:text-6xl">
              A modern web landing experience for{" "}
              <span className="bg-gradient-to-r from-vetc-300 to-vetc-500 bg-clip-text text-transparent">
                VETC Technologies
              </span>
            </h1>

            <p className="mt-6 max-w-xl text-lg text-emerald-50/70">
              Dark-green, premium visuals. Smooth scroll storytelling. 3D
              transitions that reveal key information without overwhelming the
              user.
            </p>

            <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center">
              <a
                href="#platform"
                className="rounded-2xl bg-vetc-600 px-5 py-3 text-center text-sm font-semibold text-emerald-950 shadow-glow hover:bg-vetc-500"
              >
                Explore the platform
              </a>
              <a
                href="#capabilities"
                className="rounded-2xl border border-emerald-200/10 bg-emerald-950/50 px-5 py-3 text-center text-sm font-semibold text-emerald-50 hover:border-emerald-200/20"
              >
                See key capabilities
              </a>
            </div>

            <div className="mt-10 grid grid-cols-3 gap-4">
              {[
                { v: "06+", k: "Regional zones" },
                { v: "50+", k: "FSI adopters" },
                { v: "1000+", k: "Businesses" },
              ].map((m) => (
                <div
                  key={m.k}
                  className="rounded-2xl border border-emerald-200/10 bg-emerald-950/45 p-4"
                >
                  <div className="text-2xl font-semibold text-emerald-50">
                    {m.v}
                  </div>
                  <div className="mt-1 text-xs text-emerald-100/60">{m.k}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="relative">
            <div className="absolute -left-10 -top-10 h-56 w-56 rounded-full bg-vetc-600/25 blur-3xl" />
            <div className="absolute -bottom-10 -right-10 h-64 w-64 rounded-full bg-vetc-300/20 blur-3xl" />

            <div className="relative rounded-3xl border border-emerald-200/10 bg-emerald-950/55 p-6 shadow-glow md:p-10">
              <div className="pointer-events-none absolute inset-0 bg-radial-soft opacity-90" />
              <div className="relative">
                <div className="relative overflow-hidden rounded-2xl border border-emerald-200/10 bg-emerald-950/60">
                  <Image
                    src={heroGraphic}
                    alt="VETC mobility payment network visualization"
                    className="h-44 w-full object-cover opacity-90"
                    priority
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-emerald-950/80 via-emerald-950/30 to-transparent" />
                  <div className="absolute bottom-4 left-4 right-4 flex items-center justify-between gap-4">
                    <div className="flex items-center gap-3">
                      <Image
                        src={portrait}
                        alt="Project avatar"
                        className="h-10 w-10 rounded-full border border-emerald-200/10 object-cover"
                      />
                      <div className="leading-tight">
                        <div className="text-sm font-semibold text-emerald-50">
                          Web-first product demo
                        </div>
                        <div className="text-xs text-emerald-100/60">
                          Dark-green landing • smooth motion
                        </div>
                      </div>
                    </div>
                    <div className="hidden items-center gap-2 sm:flex">
                      <span className="rounded-full border border-emerald-200/10 bg-emerald-950/60 px-3 py-1 text-xs text-emerald-50/70">
                        OpenAPI
                      </span>
                      <span className="rounded-full border border-emerald-200/10 bg-emerald-950/60 px-3 py-1 text-xs text-emerald-50/70">
                        FastAPI
                      </span>
                    </div>
                  </div>
                </div>
                <div className="text-xs tracking-[0.22em] uppercase text-emerald-100/60">
                  Product snapshot
                </div>
                <div className="mt-4 grid gap-4">
                  {[
                    {
                      title: "ETC Payments",
                      desc: "Tap-to-pass experiences with clear transaction trails.",
                      icon: billIcon,
                    },
                    {
                      title: "Digital Wallet Services",
                      desc: "Top-ups, subscriptions, and mobility add-ons in one place.",
                      icon: walletIcon,
                    },
                    {
                      title: "Open APIs",
                      desc: "Fast iterations with OpenAPI docs and Swagger UI.",
                      icon: checkReadIcon,
                    },
                  ].map((card) => (
                    <div
                      key={card.title}
                      className="rounded-2xl border border-emerald-200/10 bg-emerald-950/70 p-5 backdrop-blur"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="text-sm font-semibold text-emerald-50">
                          {card.title}
                        </div>
                        <Icon src={card.icon} alt="" className="h-5 w-5" />
                      </div>
                      <div className="mt-2 text-sm text-emerald-50/70">
                        {card.desc}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        <LoopMarquee
          items={[
            "Cashless mobility",
            "OpenAPI-first",
            "Low-latency region",
            "Data protection policy",
            "24/7 support",
            "GPU cloud ready",
            "Intelligent automation",
            "Compliance-by-design",
          ]}
        />
      </section>

      <section id="capabilities" className="py-20 md:py-28">
        <ScrollFillHeading
          eyebrow="Capabilities"
          title="Designed for speed, clarity, and trust"
          subtitle="A landing page structure that communicates value quickly, then deepens context with scroll-driven reveal."
        />

        <div className="mx-auto mt-12 grid max-w-6xl gap-6 px-6 md:grid-cols-3">
          {[
            {
              title: "Secure payment flows",
              desc: "A consistent experience from top-up to toll payment, designed with clear user feedback.",
              icon: walletIcon,
            },
            {
              title: "Operational resilience",
              desc: "Regional-first infrastructure thinking: reliability, continuity, and predictable performance.",
              icon: routingIcon,
            },
            {
              title: "Developer velocity",
              desc: "Fast iteration loops with predictable API docs and test-friendly endpoints.",
              icon: historyIcon,
            },
          ].map((f) => (
            <div
              key={f.title}
              className="rounded-3xl border border-emerald-200/10 bg-emerald-950/45 p-6 shadow-glow"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="text-lg font-semibold text-emerald-50">
                  {f.title}
                </div>
                <Icon src={f.icon} alt="" className="h-6 w-6" />
              </div>
              <div className="mt-3 text-sm leading-relaxed text-emerald-50/70">
                {f.desc}
              </div>
              <div className="mt-6 h-[1px] w-full bg-emerald-200/10" />
              <div className="mt-4 text-xs tracking-[0.22em] uppercase text-emerald-100/60">
                Built for web
              </div>
            </div>
          ))}
        </div>
      </section>

      <ThreeDShowcase />

      <section id="platform" className="py-20 md:py-28">
        <ScrollFillHeading
          eyebrow="Platform"
          title="From infrastructure to AI-ready services"
          subtitle="A narrative layout inspired by modern AI cloud experiences: crisp sections, strong contrast, and motion that supports comprehension."
        />

        <div className="mx-auto mt-12 grid max-w-6xl gap-6 px-6 md:grid-cols-2">
          {[
            {
              title: "Regional deployment mindset",
              desc: "Launch across multiple availability zones to reduce latency and strengthen business continuity.",
              icon: mapIcon,
            },
            {
              title: "Managed operations",
              desc: "Keep teams focused on product innovation while maintaining a stable, secure backbone.",
              icon: shieldIcon,
            },
            {
              title: "Intelligent automation",
              desc: "Turn documents, videos, and data into actionable insights and streamlined workflows.",
              icon: cardIcon,
            },
            {
              title: "AI/ML acceleration",
              desc: "Scale experimentation with GPU-ready infrastructure and production-grade delivery patterns.",
              icon: playIcon,
            },
          ].map((f) => (
            <div
              key={f.title}
              className="rounded-3xl border border-emerald-200/10 bg-emerald-950/45 p-6"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="text-lg font-semibold text-emerald-50">
                  {f.title}
                </div>
                <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-vetc-600/20 ring-1 ring-emerald-200/10">
                  <Icon src={f.icon} alt="" className="h-5 w-5" />
                </div>
              </div>
              <div className="mt-3 text-sm leading-relaxed text-emerald-50/70">
                {f.desc}
              </div>
            </div>
          ))}
        </div>
      </section>

      <section id="contact" className="py-20 md:py-28">
        <div className="mx-auto max-w-6xl px-6">
          <div className="overflow-hidden rounded-3xl border border-emerald-200/10 bg-emerald-950/45 shadow-glow">
            <div className="relative p-8 md:p-12">
              <div className="pointer-events-none absolute inset-0 bg-radial-soft opacity-80" />
              <div className="relative grid gap-8 md:grid-cols-2 md:items-center">
                <div>
                  <div className="text-xs tracking-[0.22em] uppercase text-emerald-100/60">
                    Contact
                  </div>
                  <h3 className="mt-4 text-3xl font-semibold text-emerald-50 md:text-4xl">
                    Ready to ship a strong demo in days, not weeks
                  </h3>
                  <p className="mt-4 text-emerald-50/70">
                    This landing structure is optimized for hackathon velocity:
                    clear messaging, reusable sections, and motion that looks
                    premium on the web.
                  </p>
                  <div className="mt-6 flex flex-wrap gap-3 text-sm text-emerald-50/70">
                    <span className="inline-flex items-center gap-2 rounded-full border border-emerald-200/10 bg-emerald-950/60 px-4 py-2">
                      <Icon src={phoneIcon} alt="" className="h-4 w-4" />
                      Hotline: 1900 6010
                    </span>
                    <span className="inline-flex items-center gap-2 rounded-full border border-emerald-200/10 bg-emerald-950/60 px-4 py-2">
                      <Icon src={mapIcon} alt="" className="h-4 w-4" />
                      Hanoi & Ho Chi Minh City
                    </span>
                    <span className="inline-flex items-center gap-2 rounded-full border border-emerald-200/10 bg-emerald-950/60 px-4 py-2">
                      <Icon src={letterIcon} alt="" className="h-4 w-4" />
                      Contact support
                    </span>
                  </div>
                </div>

                <div className="rounded-3xl border border-emerald-200/10 bg-emerald-950/60 p-6">
                  <div className="text-sm font-semibold text-emerald-50">
                    Quick links
                  </div>
                  <div className="mt-4 grid gap-3">
                    {[
                      { k: "API Docs", v: "http://localhost:8000/docs", icon: checkReadIcon },
                      { k: "ReDoc", v: "http://localhost:8000/redoc", icon: historyIcon },
                      { k: "Frontend", v: "http://localhost:3000", icon: billIcon },
                    ].map((row) => (
                      <div
                        key={row.k}
                        className="flex items-center justify-between gap-3 rounded-2xl border border-emerald-200/10 bg-emerald-950/70 px-4 py-3"
                      >
                        <span className="inline-flex items-center gap-2 text-sm text-emerald-50/80">
                          <Icon src={row.icon} alt="" className="h-4 w-4" />
                          {row.k}
                        </span>
                        <span className="truncate text-sm font-medium text-vetc-300">
                          {row.v}
                        </span>
                      </div>
                    ))}
                  </div>

                  <div className="mt-6">
                    <a
                      href="#"
                      className="inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-vetc-600 px-5 py-3 text-center text-sm font-semibold text-emerald-950 shadow-glow hover:bg-vetc-500"
                    >
                      Download demo brief
                      <Icon src={arrowRightIcon} alt="" className="h-4 w-4" />
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <footer className="mt-10 flex flex-col gap-4 border-t border-emerald-200/10 pt-8 text-sm text-emerald-100/60 md:flex-row md:items-center md:justify-between">
            <span>© {new Date().getFullYear()} VETC Technologies (concept)</span>
            <div className="flex items-center justify-between gap-6 md:justify-end">
              <span className="hidden sm:inline">
                Dark-green web landing • Scroll-driven motion • Loop slider
              </span>
              <div className="flex items-center gap-3">
                {[
                  { label: "Facebook", icon: facebookIcon, href: "#" },
                  { label: "LinkedIn", icon: linkedinIcon, href: "#" },
                  { label: "YouTube", icon: youtubeIcon, href: "#" },
                ].map((s) => (
                  <a
                    key={s.label}
                    href={s.href}
                    aria-label={s.label}
                    className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-emerald-200/10 bg-emerald-950/50 hover:border-emerald-200/20"
                  >
                    <Icon src={s.icon} alt="" className="h-5 w-5" />
                  </a>
                ))}
              </div>
            </div>
          </footer>
        </div>
      </section>
    </main>
  );
}
