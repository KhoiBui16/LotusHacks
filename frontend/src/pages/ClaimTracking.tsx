import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useLanguage } from "@/contexts/LanguageContext";
import Navbar from "@/components/landing/Navbar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { CheckCircle2, Clock, FileText, Upload, AlertTriangle, XCircle, ChevronLeft, ArrowRight, MessageSquare, Phone } from "lucide-react";

export default function ClaimTracking() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { t } = useLanguage();
  const [tab, setTab] = useState("tracking");
  const claimStatus = "processing";

  const timeline = [
    { date: "2024-12-20 14:45", label: t("ct.submitted"), status: "done" as const },
    { date: "2024-12-20 15:00", label: t("ct.docsVerified"), status: "done" as const },
    { date: "2024-12-21 09:30", label: t("ct.insurerAcknowledged"), status: "done" as const },
    { date: "2024-12-22 10:00", label: t("ct.underReviewStep"), status: "current" as const },
    { date: "", label: t("ct.surveyInspection"), status: "pending" as const },
    { date: "", label: t("ct.decision"), status: "pending" as const },
    { date: "", label: t("ct.settlement"), status: "pending" as const },
  ];

  const additionalDocs = [{ name: "Repair estimate from garage", deadline: "2024-12-25", priority: "high" }];

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container pt-24 pb-16 px-4 max-w-3xl mx-auto space-y-6">
        <Button variant="ghost" size="sm" onClick={() => navigate("/dashboard")}><ChevronLeft className="w-4 h-4 mr-1" /> {t("ct.dashboard")}</Button>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <div>
            <h1 className="text-2xl font-display font-bold text-foreground">Claim {id || "CLM-004"}</h1>
            <p className="text-sm text-muted-foreground">Collision · 51A-123.45 · Bảo Việt</p>
          </div>
          <Badge variant="outline" className="bg-yellow-500/10 border-yellow-500/30 text-yellow-400 w-fit"><Clock className="w-3 h-3 mr-1" /> {t("ct.underReview")}</Badge>
        </div>

        {additionalDocs.length > 0 && (
          <Card className="border-yellow-500/30 bg-yellow-500/5">
            <CardContent className="py-3 flex items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-yellow-400 shrink-0" />
                <div>
                  <p className="text-sm font-medium text-foreground">{t("ct.additionalDocs")}</p>
                  <p className="text-xs text-muted-foreground">{additionalDocs[0].name} · Due {additionalDocs[0].deadline}</p>
                </div>
              </div>
              <Button size="sm"><Upload className="w-3 h-3 mr-1" /> {t("cl.upload")}</Button>
            </CardContent>
          </Card>
        )}

        <Tabs value={tab} onValueChange={setTab}>
          <TabsList className="grid grid-cols-2 w-full max-w-xs">
            <TabsTrigger value="tracking">{t("ct.tracking")}</TabsTrigger>
            <TabsTrigger value="outcome">{t("ct.outcome")}</TabsTrigger>
          </TabsList>

          <TabsContent value="tracking" className="space-y-6 mt-6">
            <Card className="border-border bg-card">
              <CardHeader className="pb-2"><CardTitle className="text-base">{t("ct.claimTimeline")}</CardTitle></CardHeader>
              <CardContent>
                <div className="space-y-0">
                  {timeline.map((tl, i) => {
                    const done = tl.status === "done";
                    const current = tl.status === "current";
                    return (
                      <div key={i} className="flex gap-3">
                        <div className="flex flex-col items-center">
                          <div className={`w-3 h-3 rounded-full shrink-0 mt-1.5 ${done ? "bg-primary" : current ? "bg-yellow-400 ring-4 ring-yellow-400/20" : "bg-muted"}`} />
                          {i < timeline.length - 1 && <div className={`w-0.5 flex-1 my-1 ${done ? "bg-primary/40" : "bg-border"}`} />}
                        </div>
                        <div className="pb-6">
                          <p className={`text-sm font-medium ${done || current ? "text-foreground" : "text-muted-foreground"}`}>{tl.label}</p>
                          {tl.date && <p className="text-xs text-muted-foreground">{tl.date}</p>}
                          {current && <Badge variant="outline" className="mt-1 text-xs bg-yellow-500/10 border-yellow-500/30 text-yellow-400">{t("ct.inProgress")}</Badge>}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>

            <Card className="border-border bg-card">
              <CardHeader className="pb-2"><CardTitle className="text-base">{t("ct.currentStatus")}</CardTitle></CardHeader>
              <CardContent className="text-sm space-y-2">
                <p className="text-foreground">{t("ct.statusDesc")}</p>
                <p className="text-muted-foreground">{t("ct.statusNext")}</p>
              </CardContent>
            </Card>

            <Card className="border-border bg-card">
              <CardContent className="py-4 flex flex-col sm:flex-row gap-3">
                <Button variant="outline" className="flex-1 gap-2"><MessageSquare className="w-4 h-4" /> {t("ct.chatSupport")}</Button>
                <Button variant="outline" className="flex-1 gap-2" asChild><a href="tel:1900xxxx"><Phone className="w-4 h-4" /> {t("ct.callHotline")}</a></Button>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="outcome" className="space-y-6 mt-6">
            {claimStatus === "processing" && (
              <Card className="border-border bg-card">
                <CardContent className="py-8 flex flex-col items-center text-center gap-3">
                  <Clock className="w-10 h-10 text-yellow-400" />
                  <h3 className="text-lg font-display font-semibold text-foreground">{t("ct.pendingDecision")}</h3>
                  <p className="text-sm text-muted-foreground max-w-md">{t("ct.pendingDesc")}</p>
                </CardContent>
              </Card>
            )}
            <Card className="border-primary/30 bg-primary/5 hidden">
              <CardContent className="py-6 space-y-3">
                <div className="flex items-center gap-2"><CheckCircle2 className="w-6 h-6 text-primary" /><h3 className="text-lg font-semibold text-foreground">{t("ct.approved")}</h3></div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div><span className="text-muted-foreground">{t("ct.amount")}</span> <span className="text-foreground font-semibold">15,000,000 VND</span></div>
                  <div><span className="text-muted-foreground">{t("ct.payment")}</span> <span className="text-foreground">Bank Transfer</span></div>
                  <div><span className="text-muted-foreground">{t("ct.eta")}</span> <span className="text-foreground">5-7 business days</span></div>
                </div>
              </CardContent>
            </Card>
            <Card className="border-destructive/30 bg-destructive/5 hidden">
              <CardContent className="py-6 space-y-3">
                <div className="flex items-center gap-2"><XCircle className="w-6 h-6 text-destructive" /><h3 className="text-lg font-semibold text-foreground">{t("ct.rejected")}</h3></div>
                <p className="text-sm text-muted-foreground">{t("ct.rejectReason")}</p>
                <Button variant="outline" size="sm">{t("ct.appeal")} <ArrowRight className="w-4 h-4 ml-1" /></Button>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
