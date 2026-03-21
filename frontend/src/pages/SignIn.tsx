import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { useLanguage } from "@/contexts/LanguageContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Eye, EyeOff, Mail, Lock, ArrowLeft } from "lucide-react";
import { api } from "@/lib/api";

export default function SignIn() {
  const [isSignUp, setIsSignUp] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const { setAuth } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();

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
        },
      });
      setLoading(false);
      navigate("/");
    } catch {
      setLoading(false);
    }
  };

  const handleGoogleSignIn = () => {
    setLoading(false);
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

          <Button variant="outline" className="w-full h-11 gap-2 mb-6 border-border/60 hover:border-border hover:bg-secondary/50 active:scale-[0.98] transition-all" onClick={handleGoogleSignIn}>
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/>
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
            </svg>
            {t("signin.google")}
          </Button>

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
                {!isSignUp && <button type="button" className="text-xs text-primary hover:text-primary/80 transition-colors">{t("signin.forgot")}</button>}
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
