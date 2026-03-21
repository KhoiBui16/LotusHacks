import { useState, useEffect } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Menu, X, Globe } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { useLanguage } from "@/contexts/LanguageContext";
import UserDropdown from "@/components/landing/UserDropdown";

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const isHome = location.pathname === "/";
  const { user } = useAuth();
  const { t, toggleLang, lang } = useLanguage();

  const navLinks = [
    { label: t("nav.about"), href: "#about", type: "anchor" as const },
    { label: t("nav.features"), href: "#features", type: "anchor" as const },
    { label: t("nav.solutions"), href: "#solutions", type: "anchor" as const },
    { label: t("nav.coreServices"), href: "/core-services", type: "route" as const },
    { label: t("nav.contact"), href: "#contact", type: "anchor" as const },
  ];

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const handleAnchorClick = (href: string) => {
    setMobileOpen(false);
    if (!isHome) {
      navigate("/");
      setTimeout(() => {
        const el = document.querySelector(href);
        if (el) el.scrollIntoView({ behavior: "smooth" });
      }, 100);
      return;
    }
    const el = document.querySelector(href);
    if (el) el.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
        scrolled
          ? "bg-background/80 backdrop-blur-xl border-b border-border/50 shadow-lg shadow-primary/5"
          : "bg-transparent"
      }`}
    >
      <div className="container flex items-center justify-between h-16 md:h-20 px-4">
        <Link to="/" className="flex items-center gap-2 group shrink-0">
          <div className="w-9 h-9 rounded-lg bg-primary flex items-center justify-center font-display font-bold text-primary-foreground text-lg transition-transform duration-200 group-hover:scale-95 group-active:scale-90">
            V
          </div>
          <span className="font-display font-semibold text-lg text-foreground tracking-tight">
            VETC
          </span>
        </Link>

        <div className="hidden lg:flex items-center gap-6">
          {navLinks.map((link) =>
            link.type === "route" ? (
              <Link
                key={link.href}
                to={link.href}
                className={`text-sm transition-colors duration-200 relative after:content-[''] after:absolute after:bottom-[-2px] after:left-0 after:w-0 after:h-[2px] after:bg-primary after:transition-all after:duration-300 hover:after:w-full ${
                  location.pathname === link.href
                    ? "text-foreground after:w-full"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {link.label}
              </Link>
            ) : (
              <button
                key={link.href}
                onClick={() => handleAnchorClick(link.href)}
                className="text-sm text-muted-foreground hover:text-foreground transition-colors duration-200 relative after:content-[''] after:absolute after:bottom-[-2px] after:left-0 after:w-0 after:h-[2px] after:bg-primary after:transition-all after:duration-300 hover:after:w-full"
              >
                {link.label}
              </button>
            )
          )}
        </div>

        <div className="hidden md:flex items-center gap-3 shrink-0">
          <Button
            variant="ghost"
            size="sm"
            className="text-muted-foreground hover:text-foreground gap-1.5 px-2"
            onClick={toggleLang}
          >
            <Globe className="w-4 h-4" />
            {t("lang.toggle")}
          </Button>
          {user ? (
            <UserDropdown />
          ) : (
            <>
              <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-foreground" asChild>
                <Link to="/sign-in">{t("nav.signIn")}</Link>
              </Button>
              <Button size="sm" className="active:scale-95 transition-transform" asChild>
                <Link to="/sign-in">{t("nav.getStarted")}</Link>
              </Button>
            </>
          )}
        </div>

        <button
          className="lg:hidden p-2 text-foreground active:scale-95 transition-transform"
          onClick={() => setMobileOpen(!mobileOpen)}
        >
          {mobileOpen ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>

      {mobileOpen && (
        <div className="lg:hidden bg-background/95 backdrop-blur-xl border-t border-border animate-fade-in">
          <div className="container py-6 px-4 flex flex-col gap-4">
            {navLinks.map((link) =>
              link.type === "route" ? (
                <Link
                  key={link.href}
                  to={link.href}
                  className={`text-sm py-2 ${
                    location.pathname === link.href
                      ? "text-foreground"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                  onClick={() => setMobileOpen(false)}
                >
                  {link.label}
                </Link>
              ) : (
                <button
                  key={link.href}
                  onClick={() => handleAnchorClick(link.href)}
                  className="text-sm text-muted-foreground hover:text-foreground py-2 text-left"
                >
                  {link.label}
                </button>
              )
            )}
            <button
              onClick={toggleLang}
              className="text-sm text-muted-foreground hover:text-foreground py-2 text-left flex items-center gap-2"
            >
              <Globe className="w-4 h-4" /> {lang === "en" ? "Tiếng Việt" : "English"}
            </button>
            <div className="flex flex-col gap-2 mt-2">
              {user ? (
                <div className="flex items-center gap-2 py-2" onClick={() => setMobileOpen(false)}>
                  <UserDropdown />
                </div>
              ) : (
                <>
                  <Button variant="ghost" size="sm" className="w-full justify-center text-muted-foreground" asChild>
                    <Link to="/sign-in" onClick={() => setMobileOpen(false)}>{t("nav.signIn")}</Link>
                  </Button>
                  <Button size="sm" className="w-full" asChild>
                    <Link to="/sign-in" onClick={() => setMobileOpen(false)}>{t("nav.getStarted")}</Link>
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </nav>
  );
}
