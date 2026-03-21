import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useLanguage } from "@/contexts/LanguageContext";
import Navbar from "@/components/landing/Navbar";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Upload, Camera, CheckCircle2, AlertCircle, XCircle,
  ChevronLeft, ChevronRight, Car, ShieldAlert, MapPin, CreditCard, FileText, FileWarning, Image
} from "lucide-react";
import { TranslationKey } from "@/i18n/translations";
import { api } from "@/lib/api";
import type { ClaimDocument } from "@/lib/api";

interface DocItem {
  id: string; labelKey: TranslationKey; required: boolean; icon: React.ElementType;
  status: "pending" | "uploaded" | "error";
}

export default function ChecklistUpload() {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const qc = useQueryClient();
  const claimId = sessionStorage.getItem("activeClaimId") || "";

  const [docs, setDocs] = useState<DocItem[]>([
    { id: "vehicle-overall", labelKey: "cl.overallVehicle", required: true, icon: Car, status: "pending" },
    { id: "damage-closeup", labelKey: "cl.damageCloseup", required: true, icon: Image, status: "pending" },
    { id: "scene", labelKey: "cl.accidentScene", required: true, icon: MapPin, status: "pending" },
    { id: "registration", labelKey: "cl.registration", required: true, icon: CreditCard, status: "pending" },
    { id: "driver-license", labelKey: "cl.driverLicense", required: true, icon: FileText, status: "pending" },
    { id: "insurance-cert", labelKey: "cl.insuranceCert", required: true, icon: ShieldAlert, status: "pending" },
    { id: "police-report", labelKey: "cl.policeReport", required: false, icon: FileWarning, status: "pending" },
  ]);

  const requiredDocsQuery = useQuery({
    queryKey: ["claim-required-docs", claimId],
    queryFn: () => api.claims.requiredDocs(claimId),
    enabled: Boolean(claimId),
  });

  const uploaded = docs.filter((d) => d.status === "uploaded").length;
  const required = docs.filter((d) => d.required).length;
  const requiredDone = docs.filter((d) => d.required && d.status === "uploaded").length;
  const progress = Math.round((uploaded / docs.length) * 100);
  const minRequired = 3; // Only need 3 documents total to validate

  const documentsQuery = useQuery({
    queryKey: ["claim-documents", claimId],
    queryFn: () => api.claims.documents(claimId),
    enabled: Boolean(claimId),
  });

  useEffect(() => {
    const remoteRequired = requiredDocsQuery.data ?? [];
    if (remoteRequired.length === 0) return;
    setDocs((prev) =>
      prev.map((d) => {
        const r = remoteRequired.find((x) => x.doc_type === d.id);
        if (!r) return d;
        return { ...d, required: r.required };
      })
    );
  }, [requiredDocsQuery.data]);

  useEffect(() => {
    const remote = (documentsQuery.data ?? []) as ClaimDocument[];
    if (remote.length === 0) return;
    setDocs((prev) =>
      prev.map((d) => {
        const r = remote.find((x) => x.doc_type === d.id);
        if (!r) return d;
        const status =
          r.status === "uploaded" || r.status === "valid"
            ? "uploaded"
            : r.status === "error"
              ? "error"
              : "pending";
        return { ...d, status };
      })
    );
  }, [documentsQuery.data]);

  const uploadDoc = useMutation({
    mutationFn: async (docType: string) => {
      if (!claimId) throw new Error("No active claim");
      const file = await new Promise<File | null>((resolve) => {
        const input = document.createElement("input");
        input.type = "file";
        input.accept = "image/*,application/pdf";
        input.onchange = () => resolve(input.files?.[0] ?? null);
        input.click();
      });
      if (!file) return;
      const upload = await api.uploads.upload(file, "claim_doc");
      await api.claims.attachDocument(claimId, { doc_type: docType, upload_id: upload.upload_id });
    },
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["claim-documents", claimId] });
    },
  });

  const statusIcon = (s: DocItem["status"]) => {
    if (s === "uploaded") return <CheckCircle2 className="w-5 h-5 text-primary" />;
    if (s === "error") return <XCircle className="w-5 h-5 text-destructive" />;
    return <AlertCircle className="w-5 h-5 text-muted-foreground" />;
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container pt-24 pb-16 px-4 max-w-2xl mx-auto space-y-6">
        <Button variant="ghost" size="sm" onClick={() => navigate(-1)}><ChevronLeft className="w-4 h-4 mr-1" /> {t("cl.back")}</Button>
        <div>
          <h1 className="text-2xl font-display font-bold text-foreground">{t("cl.title")}</h1>
          <p className="text-muted-foreground mt-1">{t("cl.subtitle")}</p>
        </div>

        <Card className="border-border bg-card">
          <CardContent className="py-4 space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">{uploaded} {t("cl.of")} {docs.length} {t("cl.uploaded")}</span>
              <span className="text-foreground font-medium">{progress}%</span>
            </div>
            <Progress value={Math.min((uploaded / minRequired) * 100, 100)} className="h-2" />
            <p className="text-xs text-muted-foreground">{uploaded} {t("cl.of")} {minRequired} {t("cl.requiredDocs")}</p>
          </CardContent>
        </Card>

        <div className="space-y-3">
          {docs.map((doc) => {
            const Icon = doc.icon;
            return (
              <Card key={doc.id} className={`border transition-all ${doc.status === "error" ? "border-destructive/40" : doc.status === "uploaded" ? "border-primary/30" : "border-border"}`}>
                <CardContent className="py-3 flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${doc.status === "uploaded" ? "bg-primary/15" : doc.status === "error" ? "bg-destructive/15" : "bg-secondary"}`}>
                    <Icon className={`w-5 h-5 ${doc.status === "uploaded" ? "text-primary" : doc.status === "error" ? "text-destructive" : "text-muted-foreground"}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-foreground truncate">{t(doc.labelKey)}</span>
                    </div>
                    {doc.status === "error" && <p className="text-xs text-destructive mt-0.5">{t("cl.uploadFailed")}</p>}
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    {statusIcon(doc.status)}
                    {doc.status !== "uploaded" && (
                      <Button size="sm" variant="outline" onClick={() => uploadDoc.mutate(doc.id)} disabled={uploadDoc.isPending}><Upload className="w-3 h-3 mr-1" /> {t("cl.upload")}</Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        <Card className="border-dashed border-2 border-border hover:border-primary/40 transition-colors cursor-pointer">
          <CardContent className="py-8 flex flex-col items-center gap-3 text-center">
            <Camera className="w-8 h-8 text-muted-foreground" />
            <div>
              <p className="text-sm font-medium text-foreground">{t("cl.dragDrop")}</p>
              <p className="text-xs text-muted-foreground mt-1">{t("cl.fileTypes")}</p>
            </div>
          </CardContent>
        </Card>

        <div className="flex justify-between pt-4">
          <Button variant="outline" onClick={() => navigate(-1)}><ChevronLeft className="w-4 h-4 mr-1" /> {t("cl.back")}</Button>
          <Button onClick={() => navigate("/validation")} disabled={uploaded < minRequired}>{t("cl.validate")} <ChevronRight className="w-4 h-4 ml-1" /></Button>
        </div>
      </main>
    </div>
  );
}
