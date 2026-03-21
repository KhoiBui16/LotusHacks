import { useState } from "react";
import { Link } from "react-router-dom";
import { useLanguage } from "@/contexts/LanguageContext";
import Navbar from "@/components/landing/Navbar";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { FileText, Clock, CheckCircle2, XCircle, AlertTriangle, Plus, ChevronLeft, ChevronRight } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Search } from "lucide-react";

const allClaims = [
  { id: "CLM-004", type: "Collision", date: "2024-12-20", vehicle: "51A-123.45", insurer: "Bảo Việt", status: "processing", amount: null },
  { id: "CLM-003", type: "Scratch", date: "2024-10-10", vehicle: "30H-567.89", insurer: "PVI", status: "closed", amount: "5,000,000 VND" },
  { id: "CLM-002", type: "Glass Breakage", date: "2024-11-28", vehicle: "51A-123.45", insurer: "Bảo Việt", status: "approved", amount: "8,500,000 VND" },
  { id: "CLM-001", type: "Collision", date: "2024-12-15", vehicle: "51A-123.45", insurer: "Bảo Việt", status: "processing", amount: null },
  { id: "CLM-005", type: "Flood", date: "2024-09-05", vehicle: "43A-999.01", insurer: "PVI", status: "rejected", amount: null },
  { id: "CLM-006", type: "Part Theft", date: "2024-08-20", vehicle: "30H-567.89", insurer: "PVI", status: "draft", amount: null },
  { id: "CLM-007", type: "Scratch", date: "2024-12-18", vehicle: "51A-123.45", insurer: "Bảo Việt", status: "needs-docs", amount: null },
];

export default function Claims() {
  const { t } = useLanguage();
  const [tab, setTab] = useState("all");
  const [search, setSearch] = useState("");

  const statusConfig: Record<string, { label: string; color: string; icon: React.ElementType }> = {
    draft: { label: t("claims.draft"), color: "bg-secondary text-muted-foreground border-border", icon: FileText },
    processing: { label: t("claims.processing"), color: "bg-yellow-500/10 text-yellow-400 border-yellow-500/30", icon: Clock },
    "needs-docs": { label: t("claims.needsDocs"), color: "bg-orange-500/10 text-orange-400 border-orange-500/30", icon: AlertTriangle },
    approved: { label: t("claims.approved"), color: "bg-primary/10 text-primary border-primary/30", icon: CheckCircle2 },
    rejected: { label: t("claims.rejected"), color: "bg-destructive/10 text-destructive border-destructive/30", icon: XCircle },
    closed: { label: t("claims.closed"), color: "bg-muted-foreground/10 text-muted-foreground border-muted-foreground/30", icon: CheckCircle2 },
  };

  const tabs = [
    { value: "all", label: t("claims.all") },
    { value: "processing", label: t("claims.processing") },
    { value: "needs-docs", label: t("claims.needsDocs") },
    { value: "approved", label: t("claims.approved") },
    { value: "rejected", label: t("claims.rejected") },
    { value: "closed", label: t("claims.closed") },
    { value: "draft", label: t("claims.draft") },
  ];

  const filtered = allClaims.filter((c) => {
    if (tab !== "all" && c.status !== tab) return false;
    if (search && !c.id.toLowerCase().includes(search.toLowerCase()) && !c.type.toLowerCase().includes(search.toLowerCase()) && !c.vehicle.includes(search)) return false;
    return true;
  });

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container pt-24 pb-16 px-4 max-w-4xl mx-auto space-y-6">
        <Button variant="ghost" size="sm" asChild><Link to="/dashboard"><ChevronLeft className="w-4 h-4 mr-1" /> {t("ct.dashboard")}</Link></Button>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-display font-bold text-foreground">{t("claims.title")}</h1>
            <p className="text-muted-foreground mt-1">{allClaims.length} {t("claims.totalClaims")}</p>
          </div>
          <Button size="sm" asChild><Link to="/start-claim"><Plus className="w-4 h-4 mr-1" /> {t("claims.newClaim")}</Link></Button>
        </div>

        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input placeholder={t("claims.searchPlaceholder")} className="pl-10" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>

        <Tabs value={tab} onValueChange={setTab}>
          <TabsList className="w-full justify-start overflow-x-auto flex-nowrap">
            {tabs.map((tb) => (
              <TabsTrigger key={tb.value} value={tb.value} className="text-xs shrink-0">
                {tb.label}
                {tb.value !== "all" && <span className="ml-1 text-[10px] opacity-60">({allClaims.filter((c) => c.status === tb.value).length})</span>}
              </TabsTrigger>
            ))}
          </TabsList>
          <TabsContent value={tab} className="mt-4">
            {filtered.length === 0 ? (
              <Card className="border-border bg-card"><CardContent className="py-12 text-center"><FileText className="w-10 h-10 text-muted-foreground mx-auto mb-3" /><p className="text-sm text-muted-foreground">{t("claims.noClaims")}</p></CardContent></Card>
            ) : (
              <div className="space-y-3">
                {filtered.map((claim) => {
                  const sc = statusConfig[claim.status] || statusConfig.draft;
                  const Icon = sc.icon;
                  return (
                    <Link key={claim.id} to={`/claim-tracking/${claim.id}`}>
                      <Card className="border-border bg-card hover:bg-secondary/30 transition-colors cursor-pointer">
                        <CardContent className="py-4 flex items-center justify-between">
                          <div className="flex items-center gap-4 min-w-0">
                            <div className="w-10 h-10 rounded-lg bg-secondary flex items-center justify-center shrink-0"><Icon className="w-5 h-5 text-muted-foreground" /></div>
                            <div className="min-w-0">
                              <div className="flex items-center gap-2"><p className="text-sm font-semibold text-foreground">{claim.id}</p><span className="text-xs text-muted-foreground">· {claim.type}</span></div>
                              <p className="text-xs text-muted-foreground">{claim.vehicle} · {claim.insurer} · {claim.date}</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-3 shrink-0">
                            {claim.amount && <span className="text-sm font-medium text-foreground hidden sm:block">{claim.amount}</span>}
                            <Badge variant="outline" className={`text-xs ${sc.color}`}>{sc.label}</Badge>
                            <ChevronRight className="w-4 h-4 text-muted-foreground" />
                          </div>
                        </CardContent>
                      </Card>
                    </Link>
                  );
                })}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
