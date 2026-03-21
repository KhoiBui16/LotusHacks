import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useLanguage } from "@/contexts/LanguageContext";
import Navbar from "@/components/landing/Navbar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Car, ShieldCheck, FileText, MapPin, Clock, Users, Image, ChevronLeft, Send, CheckCircle2, Loader2 } from "lucide-react";

export default function ReviewSubmit() {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const [consent, setConsent] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = () => {
    setSubmitting(true);
    setTimeout(() => navigate("/claim-tracking/CLM-004"), 2000);
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container pt-24 pb-16 px-4 max-w-2xl mx-auto space-y-6">
        <Button variant="ghost" size="sm" onClick={() => navigate(-1)}><ChevronLeft className="w-4 h-4 mr-1" /> {t("cl.back")}</Button>
        <div>
          <h1 className="text-2xl font-display font-bold text-foreground">{t("rv.title")}</h1>
          <p className="text-muted-foreground mt-1">{t("rv.subtitle")}</p>
        </div>

        <Card className="border-border bg-card">
          <CardHeader className="pb-2"><CardTitle className="text-base flex items-center gap-2"><FileText className="w-4 h-4 text-primary" /> {t("rv.incidentSummary")}</CardTitle></CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="grid grid-cols-2 gap-3">
              <div><span className="text-muted-foreground">{t("rv.type")}</span> <span className="text-foreground ml-1">Collision</span></div>
              <div className="flex items-center gap-1"><Clock className="w-3 h-3 text-muted-foreground" /><span className="text-foreground">2024-12-20, 14:30</span></div>
              <div className="flex items-center gap-1"><MapPin className="w-3 h-3 text-muted-foreground" /><span className="text-foreground">123 Nguyen Hue, D1, HCMC</span></div>
              <div className="flex items-center gap-1"><Users className="w-3 h-3 text-muted-foreground" /><span className="text-foreground">No third party</span></div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-border bg-card">
          <CardHeader className="pb-2"><CardTitle className="text-base flex items-center gap-2"><ShieldCheck className="w-4 h-4 text-primary" /> {t("rv.policy")}</CardTitle></CardHeader>
          <CardContent className="text-sm grid grid-cols-2 gap-2">
            <div><span className="text-muted-foreground">{t("rv.vehicle")}</span> <span className="text-foreground ml-1">51A-123.45</span></div>
            <div><span className="text-muted-foreground">{t("rv.insurer")}</span> <span className="text-foreground ml-1">Bảo Việt</span></div>
            <div><span className="text-muted-foreground">{t("rv.policyLabel")}</span> <span className="text-foreground ml-1">POL-2024-00891</span></div>
            <div><span className="text-muted-foreground">{t("rv.expiry")}</span> <span className="text-foreground ml-1">2025-06-30</span></div>
          </CardContent>
        </Card>

        <Card className="border-border bg-card">
          <CardHeader className="pb-2"><CardTitle className="text-base flex items-center gap-2"><Image className="w-4 h-4 text-primary" /> {t("rv.attachments")} (6)</CardTitle></CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {[t("cl.overallVehicle"), t("cl.damageCloseup"), t("cl.accidentScene"), t("cl.registration"), t("cl.driverLicense"), t("cl.insuranceCert")].map((f) => (
                <div key={f} className="flex items-center gap-2 p-2 rounded-lg bg-secondary/40 text-xs">
                  <CheckCircle2 className="w-3 h-3 text-primary shrink-0" />
                  <span className="text-muted-foreground truncate">{f}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="border-border bg-card">
          <CardContent className="py-4">
            <label className="flex items-start gap-3 cursor-pointer">
              <Checkbox checked={consent} onCheckedChange={(c) => setConsent(c === true)} className="mt-0.5" />
              <span className="text-sm text-muted-foreground leading-relaxed">
                {t("rv.consent")} <button className="text-primary underline underline-offset-2">{t("rv.terms")}</button>.
              </span>
            </label>
          </CardContent>
        </Card>

        <div className="flex justify-between pt-4">
          <Button variant="outline" onClick={() => navigate(-1)}><ChevronLeft className="w-4 h-4 mr-1" /> {t("rv.edit")}</Button>
          <Button onClick={handleSubmit} disabled={!consent || submitting} size="lg">
            {submitting ? <><Loader2 className="w-4 h-4 mr-1 animate-spin" /> {t("rv.submitting")}</> : <><Send className="w-4 h-4 mr-1" /> {t("rv.submitClaim")}</>}
          </Button>
        </div>
      </main>
    </div>
  );
}
