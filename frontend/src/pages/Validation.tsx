import { useNavigate } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useLanguage } from "@/contexts/LanguageContext";
import Navbar from "@/components/landing/Navbar";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, XCircle, AlertTriangle, Upload, ChevronLeft, ChevronRight, RefreshCw } from "lucide-react";
import { api } from "@/lib/api";
import type { ValidationResponse, ValidationResult } from "@/lib/api";
import type { TranslationKey } from "@/i18n/translations";

export default function Validation() {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const qc = useQueryClient();
  const claimId = sessionStorage.getItem("activeClaimId") || "";

  const labelKeyByDocType: Record<string, string> = {
    "vehicle-overall": "cl.overallVehicle",
    "damage-closeup": "cl.damageCloseup",
    scene: "cl.accidentScene",
    registration: "cl.registration",
    "driver-license": "cl.driverLicense",
    "insurance-cert": "cl.insuranceCert",
    "police-report": "cl.policeReport",
  };

  const validateQuery = useQuery<ValidationResponse>({
    queryKey: ["claim-validate", claimId],
    queryFn: () => api.claims.validate(claimId),
    enabled: Boolean(claimId),
  });

  const results =
    (validateQuery.data?.results ?? []).map((r: ValidationResult) => ({
      doc_type: r.doc_type,
      name: labelKeyByDocType[r.doc_type]
        ? t(labelKeyByDocType[r.doc_type] as TranslationKey)
        : r.doc_type,
      status: r.status as "valid" | "invalid" | "missing",
      note: r.note ?? "",
    })) ?? [];

  const statusConfig = {
    valid: { icon: CheckCircle2, color: "text-primary", bg: "bg-primary/15", badge: "border-primary/30 text-primary bg-primary/10", label: t("val.valid") },
    invalid: { icon: XCircle, color: "text-destructive", bg: "bg-destructive/15", badge: "border-destructive/30 text-destructive bg-destructive/10", label: t("val.invalid") },
    missing: { icon: AlertTriangle, color: "text-yellow-400", bg: "bg-yellow-500/15", badge: "border-yellow-500/30 text-yellow-400 bg-yellow-500/10", label: t("val.missing") },
  };

  const issues = results.filter((r) => r.status !== "valid");
  const allGood = issues.length === 0;

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container pt-24 pb-16 px-4 max-w-2xl mx-auto space-y-6">
        <Button variant="ghost" size="sm" onClick={() => navigate(-1)}><ChevronLeft className="w-4 h-4 mr-1" /> {t("cl.back")}</Button>
        <div>
          <h1 className="text-2xl font-display font-bold text-foreground">{t("val.title")}</h1>
          <p className="text-muted-foreground mt-1">{t("val.subtitle")}</p>
        </div>

        <Card className={`border ${allGood ? "border-primary/30 bg-primary/5" : "border-yellow-500/30 bg-yellow-500/5"}`}>
          <CardContent className="py-4 flex items-center gap-3">
            {allGood ? (
              <><CheckCircle2 className="w-6 h-6 text-primary shrink-0" /><div><p className="font-semibold text-foreground">{t("val.allVerified")}</p><p className="text-sm text-muted-foreground">{t("val.canProceed")}</p></div></>
            ) : (
              <><AlertTriangle className="w-6 h-6 text-yellow-400 shrink-0" /><div><p className="font-semibold text-foreground">{issues.length} {t("val.issuesFound")}</p><p className="text-sm text-muted-foreground">{t("val.fixItems")}</p></div></>
            )}
          </CardContent>
        </Card>

        <div className="space-y-3">
          {results.map((r, i) => {
            const sc = statusConfig[r.status];
            const Icon = sc.icon;
            return (
              <Card key={i} className="border-border bg-card">
                <CardContent className="py-3 flex items-center gap-3">
                  <div className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${sc.bg}`}><Icon className={`w-4 h-4 ${sc.color}`} /></div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-foreground">{r.name}</p>
                    <p className="text-xs text-muted-foreground">{r.note}</p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <Badge variant="outline" className={`text-xs ${sc.badge}`}>{sc.label}</Badge>
                    {r.status !== "valid" && (
                      <Button size="sm" variant="outline" onClick={() => navigate("/checklist-upload")}><Upload className="w-3 h-3 mr-1" /> {r.status === "missing" ? t("cl.upload") : t("val.reupload")}</Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        <div className="flex justify-between pt-4">
          <Button variant="outline" onClick={() => navigate("/checklist-upload")}><ChevronLeft className="w-4 h-4 mr-1" /> {t("val.backToUpload")}</Button>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => qc.invalidateQueries({ queryKey: ["claim-validate", claimId] })} disabled={!claimId}><RefreshCw className="w-4 h-4 mr-1" /> {t("val.revalidate")}</Button>
            <Button onClick={() => navigate("/review-submit")} disabled={!allGood}>{t("val.reviewClaim")} <ChevronRight className="w-4 h-4 ml-1" /></Button>
          </div>
        </div>
      </main>
    </div>
  );
}
