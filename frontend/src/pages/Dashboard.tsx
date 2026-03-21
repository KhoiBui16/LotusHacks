import { Link } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { useLanguage } from "@/contexts/LanguageContext";
import Navbar from "@/components/landing/Navbar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Car, ShieldCheck, AlertTriangle, FileText, Bell, ArrowRight,
  Clock, CheckCircle2, XCircle, Plus, ChevronRight
} from "lucide-react";

const mockVehicle = { plate: "51A-123.45", model: "Toyota Camry 2023", policyLinked: true, policyId: "POL-2024-00891", insurer: "Bảo Việt" };
const mockClaims = [
  { id: "CLM-001", type: "Collision", date: "2024-12-15", status: "processing", vehicle: "51A-123.45" },
  { id: "CLM-002", type: "Glass Breakage", date: "2024-11-28", status: "approved", vehicle: "51A-123.45" },
  { id: "CLM-003", type: "Scratch", date: "2024-10-10", status: "closed", vehicle: "30H-567.89" },
];
const mockNotifications = [
  { id: 1, text: "CLM-001 requires additional documents", textVi: "CLM-001 cần bổ sung tài liệu", time: "2 hours ago", timeVi: "2 giờ trước", unread: true },
  { id: 2, text: "CLM-002 has been approved", textVi: "CLM-002 đã được duyệt", time: "1 day ago", timeVi: "1 ngày trước", unread: false },
];

export default function Dashboard() {
  const { user } = useAuth();
  const { t, lang } = useLanguage();

  const statusConfig: Record<string, { label: string; color: string; icon: React.ElementType }> = {
    processing: { label: t("dash.status.processing"), color: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30", icon: Clock },
    approved: { label: t("dash.status.approved"), color: "bg-primary/20 text-primary border-primary/30", icon: CheckCircle2 },
    rejected: { label: t("dash.status.rejected"), color: "bg-destructive/20 text-destructive border-destructive/30", icon: XCircle },
    closed: { label: t("dash.status.closed"), color: "bg-muted-foreground/20 text-muted-foreground border-muted-foreground/30", icon: CheckCircle2 },
    draft: { label: t("dash.status.draft"), color: "bg-secondary text-muted-foreground border-border", icon: FileText },
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container pt-24 pb-16 px-4 space-y-8">
        <div>
          <h1 className="text-2xl md:text-3xl font-display font-bold text-foreground">
            {t("dash.welcome")} <span className="text-primary">{user?.name || "User"}</span>
          </h1>
          <p className="text-muted-foreground mt-1">{t("dash.subtitle")}</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card className="lg:col-span-2 border-border bg-card">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center gap-2"><Car className="w-5 h-5 text-primary" /> {t("dash.activeVehicle")}</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div className="space-y-1">
                <p className="text-xl font-display font-bold text-foreground">{mockVehicle.plate}</p>
                <p className="text-sm text-muted-foreground">{mockVehicle.model}</p>
                <div className="flex items-center gap-2 mt-2">
                  {mockVehicle.policyLinked ? (
                    <Badge variant="outline" className="border-primary/40 text-primary bg-primary/10 gap-1">
                      <ShieldCheck className="w-3 h-3" /> {t("dash.policyLinked")}
                    </Badge>
                  ) : (
                    <Badge variant="outline" className="border-destructive/40 text-destructive bg-destructive/10 gap-1">
                      <AlertTriangle className="w-3 h-3" /> {t("dash.noPolicy")}
                    </Badge>
                  )}
                </div>
                {mockVehicle.policyLinked && (
                  <p className="text-xs text-muted-foreground mt-1">{mockVehicle.insurer} · {mockVehicle.policyId}</p>
                )}
              </div>
              <Button variant="outline" size="sm" asChild>
                <Link to="/vehicles">{t("dash.manageVehicles")} <ChevronRight className="w-4 h-4" /></Link>
              </Button>
            </CardContent>
          </Card>

          <Card className="border-primary/30 bg-gradient-to-br from-primary/10 to-primary/5 flex flex-col justify-center">
            <CardContent className="flex flex-col items-center text-center gap-4 py-8">
              <div className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center">
                <AlertTriangle className="w-8 h-8 text-primary" />
              </div>
              <div>
                <h3 className="text-lg font-display font-bold text-foreground">{t("dash.reportIncident")}</h3>
                <p className="text-sm text-muted-foreground mt-1">{t("dash.reportIncident.desc")}</p>
              </div>
              <Button className="w-full" asChild>
                <Link to="/start-claim"><Plus className="w-4 h-4 mr-1" /> {t("dash.startClaim")}</Link>
              </Button>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card className="lg:col-span-2 border-border bg-card">
            <CardHeader className="pb-3 flex flex-row items-center justify-between">
              <CardTitle className="text-lg flex items-center gap-2"><FileText className="w-5 h-5 text-primary" /> {t("dash.recentClaims")}</CardTitle>
              <Button variant="ghost" size="sm" asChild>
                <Link to="/claims">{t("dash.viewAll")} <ArrowRight className="w-4 h-4" /></Link>
              </Button>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {mockClaims.map((claim) => {
                  const sc = statusConfig[claim.status] || statusConfig.draft;
                  const Icon = sc.icon;
                  return (
                    <Link key={claim.id} to={`/claim-tracking/${claim.id}`} className="flex items-center justify-between p-3 rounded-lg bg-secondary/40 hover:bg-secondary/70 transition-colors group">
                      <div className="flex items-center gap-3 min-w-0">
                        <div className="w-9 h-9 rounded-lg bg-muted flex items-center justify-center shrink-0"><Icon className="w-4 h-4 text-muted-foreground" /></div>
                        <div className="min-w-0">
                          <p className="text-sm font-medium text-foreground truncate">{claim.id} · {claim.type}</p>
                          <p className="text-xs text-muted-foreground">{claim.vehicle} · {claim.date}</p>
                        </div>
                      </div>
                      <Badge variant="outline" className={`shrink-0 text-xs ${sc.color}`}>{sc.label}</Badge>
                    </Link>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader className="pb-3 flex flex-row items-center justify-between">
              <CardTitle className="text-lg flex items-center gap-2"><Bell className="w-5 h-5 text-primary" /> {t("dash.notifications")}</CardTitle>
              <Button variant="ghost" size="sm" asChild><Link to="/notifications">{t("dash.all")}</Link></Button>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {mockNotifications.map((n) => (
                  <div key={n.id} className={`p-3 rounded-lg text-sm ${n.unread ? "bg-primary/5 border border-primary/20" : "bg-secondary/40"}`}>
                    <p className={`${n.unread ? "text-foreground font-medium" : "text-muted-foreground"}`}>{lang === "vi" ? n.textVi : n.text}</p>
                    <p className="text-xs text-muted-foreground mt-1">{lang === "vi" ? n.timeVi : n.time}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        <Card className="border-border bg-card">
          <CardHeader className="pb-3"><CardTitle className="text-lg">{t("dash.quickActions")}</CardTitle></CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { label: t("dash.startClaim"), icon: Plus, to: "/start-claim" },
                { label: t("dash.myClaims"), icon: FileText, to: "/claims" },
                { label: t("dash.vehicles"), icon: Car, to: "/vehicles" },
                { label: t("dash.settings"), icon: Bell, to: "/settings" },
              ].map((a) => (
                <Button key={a.label} variant="outline" className="h-auto py-4 flex-col gap-2" asChild>
                  <Link to={a.to}>
                    <a.icon className="w-5 h-5 text-primary" />
                    <span className="text-xs">{a.label}</span>
                  </Link>
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
