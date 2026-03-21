import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useLanguage } from "@/contexts/LanguageContext";
import Navbar from "@/components/landing/Navbar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Car, ShieldCheck, FileText, MapPin, Clock, Users, Image, ChevronLeft, Send, CheckCircle2, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import type { Claim, ClaimDocument } from "@/lib/api";

export default function ReviewSubmit() {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const [consent, setConsent] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const claimId = sessionStorage.getItem("activeClaimId") || "";

  const claimQuery = useQuery<Claim>({
    queryKey: ["claim", claimId],
    queryFn: () => api.claims.get(claimId),
    enabled: Boolean(claimId),
  });

  const docsQuery = useQuery<ClaimDocument[]>({
    queryKey: ["claim-documents", claimId],
    queryFn: () => api.claims.documents(claimId),
    enabled: Boolean(claimId),
  });

  const submitMutation = useMutation({
    mutationFn: () => api.claims.submit(claimId),
    onSuccess: () => {
      navigate(`/claim-tracking/${claimId}`);
    },
    onSettled: () => setSubmitting(false),
  });

  const handleSubmit = () => {
    setSubmitting(true);
    submitMutation.mutate();
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
              <div>
                <span className="text-muted-foreground">{t("rv.type")}</span>{" "}
                <span className="text-foreground ml-1">{claimQuery.data?.incident?.type || "—"}</span>
              </div>
              <div className="flex items-center gap-1">
                <Clock className="w-3 h-3 text-muted-foreground" />
                <span className="text-foreground">
                  {claimQuery.data?.incident?.date || "—"}
                  {claimQuery.data?.incident?.time ? `, ${claimQuery.data?.incident?.time}` : ""}
                </span>
              </div>
              <div className="flex items-center gap-1">
                <MapPin className="w-3 h-3 text-muted-foreground" />
                <span className="text-foreground">{claimQuery.data?.incident?.location_text || "—"}</span>
              </div>
              <div className="flex items-center gap-1">
                <Users className="w-3 h-3 text-muted-foreground" />
                <span className="text-foreground">
                  {claimQuery.data?.incident?.has_third_party ? "Third party involved" : "No third party"}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-border bg-card">
          <CardHeader className="pb-2"><CardTitle className="text-base flex items-center gap-2"><ShieldCheck className="w-4 h-4 text-primary" /> {t("rv.policy")}</CardTitle></CardHeader>
          <CardContent className="text-sm grid grid-cols-2 gap-2">
            <div><span className="text-muted-foreground">{t("rv.insurer")}</span> <span className="text-foreground ml-1">{claimQuery.data?.insurer || "—"}</span></div>
            <div><span className="text-muted-foreground">{t("rv.policyLabel")}</span> <span className="text-foreground ml-1">{claimQuery.data?.policy_id || "—"}</span></div>
          </CardContent>
        </Card>

        <Card className="border-border bg-card">
          <CardHeader className="pb-2"><CardTitle className="text-base flex items-center gap-2"><Image className="w-4 h-4 text-primary" /> {t("rv.attachments")} ({(docsQuery.data ?? []).filter((d) => d.status === "uploaded" || d.status === "valid").length})</CardTitle></CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {(docsQuery.data ?? []).map((d) => (
                <div key={d.id} className="flex items-center gap-2 p-2 rounded-lg bg-secondary/40 text-xs">
                  <CheckCircle2 className="w-3 h-3 text-primary shrink-0" />
                  <span className="text-muted-foreground truncate">{d.doc_type}</span>
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
          <Button onClick={handleSubmit} disabled={!consent || submitting || !claimId} size="lg">
            {submitting ? <><Loader2 className="w-4 h-4 mr-1 animate-spin" /> {t("rv.submitting")}</> : <><Send className="w-4 h-4 mr-1" /> {t("rv.submitClaim")}</>}
          </Button>
        </div>
      </main>
    </div>
  );
}
