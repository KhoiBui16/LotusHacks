import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useLanguage } from "@/contexts/LanguageContext";
import Navbar from "@/components/landing/Navbar";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Car, Droplets, ShieldAlert, Glasses, ParkingMeter, HelpCircle,
  ChevronLeft, ChevronRight, Check, MapPin, Clock, FileText, Users, Heart
} from "lucide-react";
import { TranslationKey } from "@/i18n/translations";

export default function IncidentIntake() {
  const navigate = useNavigate();
  const { t } = useLanguage();

  const STEPS = [
    { id: "type", label: t("ii.stepType"), icon: ShieldAlert },
    { id: "time", label: t("ii.stepTime"), icon: Clock },
    { id: "location", label: t("ii.stepLocation"), icon: MapPin },
    { id: "description", label: t("ii.stepDesc"), icon: FileText },
    { id: "third-party", label: t("ii.stepThirdParty"), icon: Users },
    { id: "vehicle-condition", label: t("ii.stepVehicle"), icon: Car },
    { id: "injury", label: t("ii.stepInjury"), icon: Heart },
  ];

  const incidentTypes: { id: string; labelKey: TranslationKey; icon: typeof Car }[] = [
    { id: "collision", labelKey: "ii.collision", icon: Car },
    { id: "scratch", labelKey: "ii.scratch", icon: ParkingMeter },
    { id: "glass", labelKey: "ii.glass", icon: Glasses },
    { id: "flood", labelKey: "ii.flood", icon: Droplets },
    { id: "theft", labelKey: "ii.theft", icon: ShieldAlert },
    { id: "other", labelKey: "ii.other", icon: HelpCircle },
  ];

  const [step, setStep] = useState(0);
  const [data, setData] = useState({
    type: "", date: "", time: "", location: "", description: "",
    hasThirdParty: null as boolean | null, thirdPartyInfo: "",
    canDrive: null as boolean | null, needsTowing: null as boolean | null,
    hasInjury: null as boolean | null,
  });

  const currentStep = STEPS[step];
  const canNext = () => {
    switch (step) {
      case 0: return !!data.type;
      case 1: return !!data.date;
      case 2: return !!data.location;
      case 3: return !!data.description;
      case 4: return data.hasThirdParty !== null;
      case 5: return data.canDrive !== null;
      case 6: return data.hasInjury !== null;
      default: return true;
    }
  };

  const handleNext = () => {
    if (step < STEPS.length - 1) setStep(step + 1);
    else {
      if (data.hasInjury || data.hasThirdParty) navigate("/emergency");
      else navigate("/checklist-upload");
    }
  };

  const YesNo = ({ value, onChange }: { value: boolean | null; onChange: (v: boolean) => void }) => (
    <div className="flex gap-3">
      {[true, false].map((v) => (
        <Button key={String(v)} variant={value === v ? "default" : "outline"} className="flex-1 h-12" onClick={() => onChange(v)}>
          {v ? t("ii.yes") : t("ii.no")}
        </Button>
      ))}
    </div>
  );

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container pt-24 pb-16 px-4 max-w-3xl mx-auto">
        <div className="mb-8 overflow-x-auto">
          <div className="flex items-center gap-1 min-w-max">
            {STEPS.map((s, i) => {
              const Icon = s.icon;
              const done = i < step;
              const active = i === step;
              return (
                <div key={s.id} className="flex items-center">
                  <button onClick={() => i < step && setStep(i)} className={`flex items-center gap-1.5 px-3 py-2 rounded-full text-xs font-medium transition-all ${active ? "bg-primary text-primary-foreground" : done ? "bg-primary/20 text-primary cursor-pointer" : "bg-secondary text-muted-foreground"}`}>
                    {done ? <Check className="w-3 h-3" /> : <Icon className="w-3 h-3" />}
                    <span className="hidden sm:inline">{s.label}</span>
                  </button>
                  {i < STEPS.length - 1 && <div className={`w-4 h-0.5 mx-1 ${i < step ? "bg-primary/40" : "bg-border"}`} />}
                </div>
              );
            })}
          </div>
        </div>

        <Card className="border-border bg-card">
          <CardContent className="py-8 space-y-6">
            <div>
              <h2 className="text-xl font-display font-bold text-foreground">{currentStep.label}</h2>
              <p className="text-sm text-muted-foreground mt-1">{t("ii.step")} {step + 1} {t("ii.of")} {STEPS.length}</p>
            </div>

            {step === 0 && (
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {incidentTypes.map((it) => {
                  const Icon = it.icon;
                  return (
                    <button key={it.id} onClick={() => setData({ ...data, type: it.id })} className={`flex flex-col items-center gap-2 p-4 rounded-xl border-2 transition-all ${data.type === it.id ? "border-primary bg-primary/10" : "border-border hover:border-primary/40 bg-secondary/30"}`}>
                      <Icon className={`w-6 h-6 ${data.type === it.id ? "text-primary" : "text-muted-foreground"}`} />
                      <span className={`text-sm font-medium ${data.type === it.id ? "text-foreground" : "text-muted-foreground"}`}>{t(it.labelKey)}</span>
                    </button>
                  );
                })}
              </div>
            )}

            {step === 1 && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-2"><Label>{t("ii.date")}</Label><Input type="date" value={data.date} onChange={(e) => setData({ ...data, date: e.target.value })} /></div>
                <div className="space-y-2"><Label>{t("ii.time")}</Label><Input type="time" value={data.time} onChange={(e) => setData({ ...data, time: e.target.value })} /></div>
              </div>
            )}

            {step === 2 && (
              <div className="space-y-4">
                <div className="space-y-2"><Label>{t("ii.locationLabel")}</Label><Input placeholder={t("ii.locationPlaceholder")} value={data.location} onChange={(e) => setData({ ...data, location: e.target.value })} /></div>
                <Button variant="outline" size="sm"><MapPin className="w-4 h-4 mr-1" /> {t("ii.useCurrentLocation")}</Button>
                <div className="w-full h-48 rounded-lg bg-secondary/60 border border-border flex items-center justify-center text-muted-foreground text-sm">{t("ii.mapPlaceholder")}</div>
              </div>
            )}

            {step === 3 && (
              <div className="space-y-2">
                <Label>{t("ii.describeLabel")}</Label>
                <Textarea placeholder={t("ii.describePlaceholder")} rows={5} value={data.description} onChange={(e) => setData({ ...data, description: e.target.value })} />
                <p className="text-xs text-muted-foreground">{t("ii.describeHint")}</p>
              </div>
            )}

            {step === 4 && (
              <div className="space-y-4">
                <Label>{t("ii.thirdPartyQ")}</Label>
                <YesNo value={data.hasThirdParty} onChange={(v) => setData({ ...data, hasThirdParty: v })} />
                {data.hasThirdParty && (
                  <div className="space-y-2 animate-in fade-in duration-200">
                    <Label>{t("ii.thirdPartyDetails")}</Label>
                    <Textarea placeholder={t("ii.thirdPartyPlaceholder")} rows={3} value={data.thirdPartyInfo} onChange={(e) => setData({ ...data, thirdPartyInfo: e.target.value })} />
                  </div>
                )}
              </div>
            )}

            {step === 5 && (
              <div className="space-y-6">
                <div className="space-y-3"><Label>{t("ii.canDriveQ")}</Label><YesNo value={data.canDrive} onChange={(v) => setData({ ...data, canDrive: v })} /></div>
                {data.canDrive === false && (
                  <div className="space-y-3 animate-in fade-in duration-200"><Label>{t("ii.towingQ")}</Label><YesNo value={data.needsTowing} onChange={(v) => setData({ ...data, needsTowing: v })} /></div>
                )}
              </div>
            )}

            {step === 6 && (
              <div className="space-y-4">
                <Label>{t("ii.injuryQ")}</Label>
                <YesNo value={data.hasInjury} onChange={(v) => setData({ ...data, hasInjury: v })} />
                {data.hasInjury && (
                  <div className="p-4 rounded-lg bg-destructive/10 border border-destructive/30 animate-in fade-in duration-200">
                    <p className="text-sm font-medium text-destructive">{t("ii.injuryWarning")}</p>
                  </div>
                )}
              </div>
            )}

            <div className="flex justify-between pt-4">
              <Button variant="outline" onClick={() => step > 0 ? setStep(step - 1) : navigate("/start-claim")}>
                <ChevronLeft className="w-4 h-4 mr-1" /> {step > 0 ? t("ii.back") : t("ii.cancel")}
              </Button>
              <Button onClick={handleNext} disabled={!canNext()}>
                {step < STEPS.length - 1 ? t("ii.next") : t("ii.continue")} <ChevronRight className="w-4 h-4 ml-1" />
              </Button>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
