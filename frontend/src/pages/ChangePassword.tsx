import { useState } from "react";
import { Link } from "react-router-dom";
import { useLanguage } from "@/contexts/LanguageContext";
import Navbar from "@/components/landing/Navbar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { ChevronLeft, Lock, Eye, EyeOff, CheckCircle2, AlertTriangle, ShieldCheck } from "lucide-react";

export default function ChangePassword() {
  const { t } = useLanguage();
  const [current, setCurrent] = useState("");
  const [newPw, setNewPw] = useState("");
  const [confirm, setConfirm] = useState("");
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [status, setStatus] = useState<"idle" | "success" | "error">("idle");
  const [error, setError] = useState("");

  const checks = [
    { label: t("cp.min8"), ok: newPw.length >= 8 },
    { label: t("cp.uppercase"), ok: /[A-Z]/.test(newPw) },
    { label: t("cp.lowercase"), ok: /[a-z]/.test(newPw) },
    { label: t("cp.number"), ok: /\d/.test(newPw) },
    { label: t("cp.special"), ok: /[!@#$%^&*(),.?":{}|<>]/.test(newPw) },
  ];

  const allValid = checks.every((c) => c.ok);
  const passwordsMatch = newPw === confirm && confirm.length > 0;
  const canSubmit = current.length > 0 && allValid && passwordsMatch;

  const handleSubmit = () => {
    if (!canSubmit) return;
    if (current === "wrong") {
      setStatus("error");
      setError(t("cp.wrongCurrent"));
      return;
    }
    setStatus("success");
    setCurrent("");
    setNewPw("");
    setConfirm("");
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container pt-24 pb-16 px-4 max-w-lg mx-auto space-y-6">
        <Button variant="ghost" size="sm" asChild>
          <Link to="/settings">
            <ChevronLeft className="w-4 h-4 mr-1" /> {t("cp.backSettings")}
          </Link>
        </Button>

        <div>
          <h1 className="text-2xl font-display font-bold text-foreground flex items-center gap-2">
            <Lock className="w-6 h-6 text-primary" /> {t("cp.title")}
          </h1>
          <p className="text-muted-foreground mt-1">{t("cp.subtitle")}</p>
        </div>

        {status === "success" && (
          <Alert className="border-primary/30 bg-primary/5">
            <CheckCircle2 className="w-4 h-4 text-primary" />
            <AlertDescription className="text-primary font-medium">{t("cp.success")}</AlertDescription>
          </Alert>
        )}

        {status === "error" && (
          <Alert variant="destructive">
            <AlertTriangle className="w-4 h-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <Card className="border-border bg-card">
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-primary" /> {t("cp.updatePassword")}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-5">
            {/* Current Password */}
            <div className="space-y-2">
              <Label>{t("cp.currentPassword")}</Label>
              <div className="relative">
                <Input
                  type={showCurrent ? "text" : "password"}
                  value={current}
                  onChange={(e) => { setCurrent(e.target.value); setStatus("idle"); }}
                  placeholder="••••••••"
                />
                <button type="button" onClick={() => setShowCurrent(!showCurrent)} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors">
                  {showCurrent ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* New Password */}
            <div className="space-y-2">
              <Label>{t("cp.newPassword")}</Label>
              <div className="relative">
                <Input
                  type={showNew ? "text" : "password"}
                  value={newPw}
                  onChange={(e) => { setNewPw(e.target.value); setStatus("idle"); }}
                  placeholder="••••••••"
                />
                <button type="button" onClick={() => setShowNew(!showNew)} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors">
                  {showNew ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>

              {/* Strength checks */}
              {newPw.length > 0 && (
                <div className="space-y-1.5 pt-1">
                  {checks.map((c) => (
                    <div key={c.label} className="flex items-center gap-2 text-xs">
                      <CheckCircle2 className={`w-3.5 h-3.5 ${c.ok ? "text-primary" : "text-muted-foreground/40"}`} />
                      <span className={c.ok ? "text-foreground" : "text-muted-foreground"}>{c.label}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Confirm Password */}
            <div className="space-y-2">
              <Label>{t("cp.confirmPassword")}</Label>
              <div className="relative">
                <Input
                  type={showConfirm ? "text" : "password"}
                  value={confirm}
                  onChange={(e) => { setConfirm(e.target.value); setStatus("idle"); }}
                  placeholder="••••••••"
                />
                <button type="button" onClick={() => setShowConfirm(!showConfirm)} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors">
                  {showConfirm ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {confirm.length > 0 && !passwordsMatch && (
                <p className="text-xs text-destructive">{t("cp.mismatch")}</p>
              )}
              {passwordsMatch && (
                <p className="text-xs text-primary flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> {t("cp.match")}
                </p>
              )}
            </div>

            <Button onClick={handleSubmit} disabled={!canSubmit} className="w-full" size="lg">
              {t("cp.submit")}
            </Button>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
