import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { useLanguage } from "@/contexts/LanguageContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Eye, EyeOff, Mail, Lock, ArrowLeft } from "lucide-react";
import { api } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

export default function SignIn() {
  const [isSignUp, setIsSignUp] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const { setAuth, user, accessToken } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const { toast } = useToast();
  const googleButtonRef = useRef<HTMLDivElement | null>(null);

  const googleClientId = useMemo(() => {
    const v = import.meta.env.VITE_GOOGLE_CLIENT_ID;
    return v && v.trim() ? v.trim() : "";
  }, []);

  useEffect(() => {
    if (user && accessToken) {
      navigate("/", { replace: true });
    }
  }, [user, accessToken, navigate]);

  useEffect(() => {
    if (!googleClientId) return;
    if (!googleButtonRef.current) return;

    const existing = document.querySelector<HTMLScriptElement>(
      'script[src="https://accounts.google.com/gsi/client"]'
    );

    const ensureScript = () =>
      new Promise<void>((resolve, reject) => {
        if (existing) {
          if (window.google?.accounts?.id) resolve();
          else existing.addEventListener("load", () => resolve(), { once: true });
          return;
        }
        const s = document.createElement("script");
        s.src = "https://accounts.google.com/gsi/client";
        s.async = true;
        s.defer = true;
        s.onload = () => resolve();
        s.onerror = () => reject(new Error("Failed to load Google script"));
        document.head.appendChild(s);
      });

    let cancelled = false;

    ensureScript()
      .then(() => {
        if (cancelled) return;
        if (!window.google?.accounts?.id) return;

        window.google.accounts.id.initialize({
          client_id: googleClientId,
          callback: async (response) => {
            try {
              if (!response.credential) {
                throw new Error("Missing Google credential");
              }
              setLoading(true);
              const resp = await api.auth.google({ id_token: response.credential });
              setAuth({
                accessToken: resp.access_token,
                user: {
                  id: resp.user.id,
                  name: resp.user.full_name || resp.user.email.split("@")[0],
                  email: resp.user.email,
                  avatar: resp.user.avatar_url ?? undefined,
                  role: resp.user.role ?? "user",
                },
              });
              navigate("/", { replace: true });
            } catch (err) {
              toast({
                title: "Google sign-in failed",
                description: err instanceof Error ? err.message : "Please try again.",
                variant: "destructive",
              });
            } finally {
              setLoading(false);
            }
          },
          cancel_on_tap_outside: true,
        });

        googleButtonRef.current.innerHTML = "";
        window.google.accounts.id.renderButton(googleButtonRef.current, {
          theme: "outline",
          size: "large",
          width: "100%",
          text: "continue_with",
          shape: "pill",
          logo_alignment: "left",
        });
      })
      .catch(() => {
        toast({
          title: "Google sign-in unavailable",
          description: "Failed to load Google sign-in script.",
          variant: "destructive",
        });
      });

    return () => {
      cancelled = true;
    };
  }, [googleClientId, navigate, setAuth, toast]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const resp = isSignUp
        ? await api.auth.signup({ email, full_name: name, password })
        : await api.auth.signin({ email, password });

      setAuth({
        accessToken: resp.access_token,
        user: {
          id: resp.user.id,
          name: resp.user.full_name || resp.user.email.split("@")[0],
          email: resp.user.email,
          avatar: resp.user.avatar_url ?? undefined,
          role: resp.user.role ?? "user",
        },
      });
      setLoading(false);
      navigate("/", { replace: true });
    } catch (err) {
      setLoading(false);
      toast({
        title: isSignUp ? "Sign up failed" : "Sign in failed",
        description: err instanceof Error ? err.message : "Please try again.",
        variant: "destructive",
      });
    }
  };

  return (
    <div className="min-h-screen bg-background flex">
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden items-center justify-center bg-gradient-to-br from-primary/20 via-background to-secondary">
        <div className="absolute inset-0">
          <div className="absolute top-1/4 left-1/4 w-72 h-72 bg-primary/10 rounded-full blur-3xl animate-pulse" />
          <div className="absolute bottom-1/3 right-1/4 w-96 h-96 bg-primary/5 rounded-full blur-3xl animate-pulse" style={{ animationDelay: "1.5s" }} />
        </div>
        <div className="relative z-10 px-12 max-w-lg">
          <Link to="/" className="flex items-center gap-3 mb-12 group">
            <div className="w-12 h-12 rounded-xl bg-primary flex items-center justify-center font-display font-bold text-primary-foreground text-xl transition-transform duration-200 group-hover:scale-95">V</div>
            <span className="font-display font-semibold text-2xl text-foreground tracking-tight">VETC</span>
          </Link>
          <h2 className="font-display text-3xl font-bold text-foreground leading-tight mb-4" style={{ lineHeight: "1.15" }}>
            {t("signin.brand.title1")}<br />
            <span className="text-primary">{t("signin.brand.title2")}</span>
          </h2>
          <p className="text-muted-foreground leading-relaxed">{t("signin.brand.subtitle")}</p>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center p-6 sm:p-10">
        <div className="w-full max-w-md">
          <Link to="/" className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors mb-8 lg:hidden">
            <ArrowLeft size={16} />{t("signin.back")}
          </Link>
          <div className="lg:hidden flex items-center gap-2 mb-8">
            <div className="w-9 h-9 rounded-lg bg-primary flex items-center justify-center font-display font-bold text-primary-foreground text-lg">V</div>
            <span className="font-display font-semibold text-lg text-foreground tracking-tight">VETC</span>
          </div>

          <h1 className="font-display text-2xl font-bold text-foreground mb-1" style={{ lineHeight: "1.2" }}>
            {isSignUp ? t("signin.title.signup") : t("signin.title.login")}
          </h1>
          <p className="text-muted-foreground text-sm mb-8">
            {isSignUp ? t("signin.subtitle.signup") : t("signin.subtitle.login")}
          </p>

          <div className="mb-6">
            {googleClientId ? (
              <div ref={googleButtonRef} />
            ) : (
              <Button
                variant="outline"
                className="w-full h-11 gap-2 border-border/60 hover:border-border hover:bg-secondary/50 active:scale-[0.98] transition-all"
                onClick={() =>
                  toast({
                    title: "Google sign-in unavailable",
                    description: "Set VITE_GOOGLE_CLIENT_ID to enable Google sign-in.",
                    variant: "destructive",
                  })
                }
              >
                {t("signin.google")}
              </Button>
            )}
          </div>

          <div className="flex items-center gap-3 mb-6">
            <div className="flex-1 h-px bg-border/50" />
            <span className="text-xs text-muted-foreground uppercase tracking-wider">{t("signin.or")}</span>
            <div className="flex-1 h-px bg-border/50" />
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {isSignUp && (
              <div className="space-y-2">
                <Label htmlFor="name" className="text-sm text-foreground">{t("signin.name")}</Label>
                <Input id="name" placeholder={t("signin.name.placeholder")} value={name} onChange={(e) => setName(e.target.value)} className="h-11 bg-secondary/40 border-border/50 focus:border-primary/50 placeholder:text-muted-foreground/60" required />
              </div>
            )}
            <div className="space-y-2">
              <Label htmlFor="email" className="text-sm text-foreground">{t("signin.email")}</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground/60" size={16} />
                <Input id="email" type="email" placeholder={t("signin.email.placeholder")} value={email} onChange={(e) => setEmail(e.target.value)} className="h-11 pl-10 bg-secondary/40 border-border/50 focus:border-primary/50 placeholder:text-muted-foreground/60" required />
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="password" className="text-sm text-foreground">{t("signin.password")}</Label>
                {!isSignUp && (
                  <button
                    type="button"
                    className="text-xs text-primary hover:text-primary/80 transition-colors"
                    onClick={() => navigate("/forgot-password")}
                  >
                    {t("signin.forgot")}
                  </button>
                )}
              </div>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground/60" size={16} />
                <Input id="password" type={showPassword ? "text" : "password"} placeholder="••••••••" value={password} onChange={(e) => setPassword(e.target.value)} className="h-11 pl-10 pr-10 bg-secondary/40 border-border/50 focus:border-primary/50 placeholder:text-muted-foreground/60" required minLength={8} />
                <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground/60 hover:text-muted-foreground transition-colors">
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>
            <Button type="submit" className="w-full h-11 font-medium active:scale-[0.98] transition-all" disabled={loading}>
              {loading ? (
                <span className="flex items-center gap-2">
                  <span className="w-4 h-4 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
                  {isSignUp ? t("signin.loading.signup") : t("signin.loading.login")}
                </span>
              ) : (
                isSignUp ? t("signin.submit.signup") : t("signin.submit.login")
              )}
            </Button>
          </form>

          <p className="text-sm text-muted-foreground text-center mt-6">
            {isSignUp ? t("signin.toggle.login") : t("signin.toggle.signup")}{" "}
            <button type="button" onClick={() => setIsSignUp(!isSignUp)} className="text-primary hover:text-primary/80 font-medium transition-colors">
              {isSignUp ? t("signin.submit.login") : t("signin.submit.signup")}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
