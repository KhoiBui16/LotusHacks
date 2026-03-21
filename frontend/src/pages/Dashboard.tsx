import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
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
import { api } from "@/lib/api";
import type { ClaimListItem, NotificationItem, VehicleSummary } from "@/lib/api";
import AdminDashboard from "./AdminDashboard";

function timeAgo(iso: string) {
  const ms = Date.now() - new Date(iso).getTime();
  const mins = Math.max(0, Math.floor(ms / 60000));
  if (mins < 60) return `${mins} min ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} hours ago`;
  const days = Math.floor(hours / 24);
  return `${days} days ago`;
}

export default function Dashboard() {
  const { user } = useAuth();
  const { t } = useLanguage();

  if (user?.role === "admin") {
    return <AdminDashboard />;
  }

  const vehiclesQuery = useQuery<VehicleSummary[]>({
    queryKey: ["vehicles"],
    queryFn: api.vehicles.list,
  });

  const claimsQuery = useQuery<ClaimListItem[]>({
    queryKey: ["claims", "dashboard"],
    queryFn: () => api.claims.list({}),
  });

  const notificationsQuery = useQuery<NotificationItem[]>({
    queryKey: ["notifications", "dashboard"],
    queryFn: () => api.notifications.list("all"),
  });

  const activeVehicle = (vehiclesQuery.data ?? [])[0];
  const recentClaims = (claimsQuery.data ?? []).slice(0, 3);
  const recentNotifications = (notificationsQuery.data ?? []).slice(0, 3);

  const statusConfig: Record<string, { label: string; color: string; icon: React.ElementType }> = {
    processing: { label: t("dash.status.processing"), color: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30", icon: Clock },
    approved: { label: t("dash.status.approved"), color: "bg-primary/20 text-primary border-primary/30", icon: CheckCircle2 },
    rejected: { label: t("dash.status.rejected"), color: "bg-destructive/20 text-destructive border-destructive/30", icon: XCircle },
    closed: { label: t("dash.status.closed"), color: "bg-muted-foreground/20 text-muted-foreground border-muted-foreground/30", icon: CheckCircle2 },
    draft: { label: t("dash.status.draft"), color: "bg-secondary text-muted-foreground border-border", icon: FileText },
    "needs-docs": { label: "Needs Docs", color: "bg-orange-500/20 text-orange-400 border-orange-500/30", icon: AlertTriangle },
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
              {activeVehicle ? (
                <>
                  <div className="space-y-1">
                    <p className="text-xl font-display font-bold text-foreground">{activeVehicle.plate || "—"}</p>
                    <p className="text-sm text-muted-foreground">{activeVehicle.model} {activeVehicle.year}</p>
                    <div className="flex items-center gap-2 mt-2">
                      {activeVehicle.policy_linked ? (
                        <Badge variant="outline" className="border-primary/40 text-primary bg-primary/10 gap-1">
                          <ShieldCheck className="w-3 h-3" /> {t("dash.policyLinked")}
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="border-destructive/40 text-destructive bg-destructive/10 gap-1">
                          <AlertTriangle className="w-3 h-3" /> {t("dash.noPolicy")}
                        </Badge>
                      )}
                    </div>
                    {activeVehicle.policy_linked && (
                      <p className="text-xs text-muted-foreground mt-1">{activeVehicle.insurer || "—"} · {activeVehicle.policy_id || "—"}</p>
                    )}
                  </div>
                  <Button variant="outline" size="sm" asChild>
                    <Link to="/vehicles">{t("dash.manageVehicles")} <ChevronRight className="w-4 h-4" /></Link>
                  </Button>
                </>
              ) : (
                <div className="w-full flex items-center justify-between gap-3">
                  <p className="text-sm text-muted-foreground">No vehicle found. Add your first vehicle to continue.</p>
                  <Button size="sm" asChild>
                    <Link to="/vehicles#add"><Plus className="w-4 h-4 mr-1" /> {t("vh.addVehicle")}</Link>
                  </Button>
                </div>
              )}
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
                {recentClaims.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No claim yet.</p>
                ) : (
                  recentClaims.map((claim) => {
                    const sc = statusConfig[claim.status] || statusConfig.draft;
                    const Icon = sc.icon;
                    return (
                      <Link key={claim.id} to={`/claim-tracking/${claim.id}`} className="flex items-center justify-between p-3 rounded-lg bg-secondary/40 hover:bg-secondary/70 transition-colors group">
                        <div className="flex items-center gap-3 min-w-0">
                          <div className="w-9 h-9 rounded-lg bg-muted flex items-center justify-center shrink-0"><Icon className="w-4 h-4 text-muted-foreground" /></div>
                          <div className="min-w-0">
                            <p className="text-sm font-medium text-foreground truncate">{claim.id.slice(-8)} · {claim.type}</p>
                            <p className="text-xs text-muted-foreground">{claim.vehicle_plate || "—"} · {claim.date}</p>
                          </div>
                        </div>
                        <Badge variant="outline" className={`shrink-0 text-xs ${sc.color}`}>{sc.label}</Badge>
                      </Link>
                    );
                  })
                )}
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
                {recentNotifications.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No notification.</p>
                ) : (
                  recentNotifications.map((n) => (
                    <div key={n.id} className={`p-3 rounded-lg text-sm ${!n.read ? "bg-primary/5 border border-primary/20" : "bg-secondary/40"}`}>
                      <p className={`${!n.read ? "text-foreground font-medium" : "text-muted-foreground"}`}>{n.title}</p>
                      <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{n.message}</p>
                      <p className="text-xs text-muted-foreground mt-1">{timeAgo(n.created_at)}</p>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        <Card className="border-border bg-card">
          <CardHeader className="pb-3"><CardTitle className="text-lg">{t("dash.quickActions")}</CardTitle></CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
              {[
                { label: t("dash.startClaim"), icon: Plus, to: "/start-claim" },
                { label: t("vh.addVehicle"), icon: Car, to: "/vehicles#add" },
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
