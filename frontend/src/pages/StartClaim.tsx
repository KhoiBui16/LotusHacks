import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useLanguage } from "@/contexts/LanguageContext";
import Navbar from "@/components/landing/Navbar";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Car, ShieldCheck, AlertTriangle, Upload, ArrowRight, CheckCircle2, ChevronLeft } from "lucide-react";

const mockVehicles = [
  { id: "v1", plate: "51A-123.45", model: "Toyota Camry 2023", policyLinked: true, policyId: "POL-2024-00891", insurer: "Bảo Việt", expiry: "2025-06-30" },
  { id: "v2", plate: "30H-567.89", model: "Honda CR-V 2022", policyLinked: false, policyId: null, insurer: null, expiry: null },
];

export default function StartClaim() {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const [selectedVehicle, setSelectedVehicle] = useState<string | null>(null);
  const [showImport, setShowImport] = useState(false);
  const vehicle = mockVehicles.find((v) => v.id === selectedVehicle);

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container pt-24 pb-16 px-4 max-w-2xl mx-auto space-y-6">
        <Button variant="ghost" size="sm" asChild><Link to="/dashboard"><ChevronLeft className="w-4 h-4 mr-1" /> {t("sc.back")}</Link></Button>
        <div>
          <h1 className="text-2xl font-display font-bold text-foreground">{t("sc.title")}</h1>
          <p className="text-muted-foreground mt-1">{t("sc.subtitle")}</p>
        </div>
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">{t("sc.step1")}</h2>
          <div className="grid gap-3">
            {mockVehicles.map((v) => (
              <Card key={v.id} className={`cursor-pointer transition-all border-2 ${selectedVehicle === v.id ? "border-primary bg-primary/5" : "border-border hover:border-primary/40"}`} onClick={() => { setSelectedVehicle(v.id); setShowImport(false); }}>
                <CardContent className="flex items-center justify-between py-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-secondary flex items-center justify-center"><Car className="w-5 h-5 text-primary" /></div>
                    <div>
                      <p className="font-display font-bold text-foreground">{v.plate}</p>
                      <p className="text-sm text-muted-foreground">{v.model}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {v.policyLinked ? (
                      <Badge variant="outline" className="border-primary/40 text-primary bg-primary/10 gap-1 text-xs"><ShieldCheck className="w-3 h-3" /> {t("sc.linked")}</Badge>
                    ) : (
                      <Badge variant="outline" className="border-yellow-500/40 text-yellow-400 bg-yellow-500/10 gap-1 text-xs"><AlertTriangle className="w-3 h-3" /> {t("sc.noPolicy")}</Badge>
                    )}
                    {selectedVehicle === v.id && <CheckCircle2 className="w-5 h-5 text-primary" />}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {vehicle && (
          <div className="space-y-3 animate-in fade-in slide-in-from-bottom-2 duration-300">
            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">{t("sc.step2")}</h2>
            {vehicle.policyLinked ? (
              <Card className="border-primary/30 bg-primary/5">
                <CardContent className="py-4 space-y-2">
                  <div className="flex items-center gap-2"><ShieldCheck className="w-5 h-5 text-primary" /><span className="font-semibold text-foreground">{t("sc.policyActive")}</span></div>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div><span className="text-muted-foreground">{t("sc.insurer")}</span> <span className="text-foreground">{vehicle.insurer}</span></div>
                    <div><span className="text-muted-foreground">{t("sc.policyId")}</span> <span className="text-foreground">{vehicle.policyId}</span></div>
                    <div><span className="text-muted-foreground">{t("sc.expiry")}</span> <span className="text-foreground">{vehicle.expiry}</span></div>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card className="border-yellow-500/30 bg-yellow-500/5">
                <CardContent className="py-4 space-y-3">
                  <div className="flex items-center gap-2"><AlertTriangle className="w-5 h-5 text-yellow-400" /><span className="font-semibold text-foreground">{t("sc.noPolicyLinked")}</span></div>
                  <p className="text-sm text-muted-foreground">{t("sc.noPolicyDesc")}</p>
                  {!showImport ? (
                    <Button variant="outline" size="sm" onClick={() => setShowImport(true)}><Upload className="w-4 h-4 mr-1" /> {t("sc.importPolicy")}</Button>
                  ) : (
                    <div className="space-y-3 animate-in fade-in duration-200">
                      <Input placeholder={t("sc.enterPolicy")} />
                      <p className="text-xs text-muted-foreground">{t("sc.orUpload")}</p>
                      <div className="border-2 border-dashed border-border rounded-lg p-6 text-center hover:border-primary/40 transition-colors cursor-pointer">
                        <Upload className="w-8 h-8 text-muted-foreground mx-auto mb-2" />
                        <p className="text-sm text-muted-foreground">{t("sc.dropFile")}</p>
                      </div>
                      <Button size="sm">{t("sc.linkPolicy")}</Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {vehicle?.policyLinked && (
          <div className="pt-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
            <Button className="w-full" size="lg" onClick={() => navigate("/incident-intake")}>
              {t("sc.continue")} <ArrowRight className="w-4 h-4 ml-1" />
            </Button>
          </div>
        )}
      </main>
    </div>
  );
}
