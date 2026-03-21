import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Navbar from "@/components/landing/Navbar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { Bell, ChevronRight, FileText, Search } from "lucide-react";

const STATUS_OPTIONS = ["processing", "needs-docs", "approved", "rejected", "closed"];

function timeAgo(iso: string) {
  const ms = Date.now() - new Date(iso).getTime();
  const mins = Math.max(0, Math.floor(ms / 60000));
  if (mins < 60) return `${mins} min ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} hours ago`;
  return `${Math.floor(hours / 24)} days ago`;
}

export default function AdminDashboard() {
  const [status, setStatus] = useState("all");
  const [q, setQ] = useState("");
  const qc = useQueryClient();
  const { toast } = useToast();

  const claimsQuery = useQuery({
    queryKey: ["admin-claims", status, q],
    queryFn: () => api.admin.listClaims({ status: status === "all" ? undefined : status, q: q || undefined }),
  });

  const notificationsQuery = useQuery({
    queryKey: ["notifications", "admin-dashboard"],
    queryFn: () => api.notifications.list("unread"),
  });

  const statusMutation = useMutation({
    mutationFn: ({ claimId, nextStatus }: { claimId: string; nextStatus: string }) =>
      api.admin.updateClaimStatus(claimId, { status: nextStatus }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["admin-claims"] });
      await qc.invalidateQueries({ queryKey: ["notifications"] });
      toast({ title: "Claim updated", description: "Claim status has been updated." });
    },
    onError: (err) => {
      toast({
        title: "Update failed",
        description: err instanceof Error ? err.message : "Could not update claim status.",
        variant: "destructive",
      });
    },
  });

  const claims = claimsQuery.data ?? [];
  const unread = notificationsQuery.data ?? [];

  const counts = useMemo(() => {
    const acc: Record<string, number> = { all: claims.length };
    for (const c of claims) acc[c.status] = (acc[c.status] ?? 0) + 1;
    return acc;
  }, [claims]);

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container pt-24 pb-16 px-4 max-w-6xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-display font-bold text-foreground">Admin Claims Dashboard</h1>
          <p className="text-muted-foreground mt-1">Review incoming user claims and process statuses.</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card className="lg:col-span-2 border-border bg-card">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center gap-2">
                <FileText className="w-5 h-5 text-primary" /> Claims Queue
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex flex-wrap gap-2">
                {["all", "processing", "needs-docs", "approved", "rejected", "closed", "draft"].map((s) => (
                  <Button key={s} size="sm" variant={status === s ? "default" : "outline"} onClick={() => setStatus(s)}>
                    {s} ({counts[s] ?? 0})
                  </Button>
                ))}
              </div>

              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input value={q} onChange={(e) => setQ(e.target.value)} className="pl-10" placeholder="Search by user, email, claim id, plate" />
              </div>

              <div className="space-y-3">
                {claims.length === 0 ? (
                  <p className="text-sm text-muted-foreground py-4">No claims found.</p>
                ) : (
                  claims.map((claim) => (
                    <Card key={claim.id} className="border-border bg-secondary/20">
                      <CardContent className="py-4 space-y-3">
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <p className="text-sm font-semibold text-foreground">{claim.id.slice(-8)} · {claim.type}</p>
                            <p className="text-xs text-muted-foreground">{claim.user_name} ({claim.user_email})</p>
                            <p className="text-xs text-muted-foreground">{claim.vehicle_plate || "—"} · {claim.date} · {claim.insurer || "No insurer"}</p>
                          </div>
                          <Badge variant="outline">{claim.status}</Badge>
                        </div>

                        <div className="flex flex-wrap gap-2">
                          {STATUS_OPTIONS.map((next) => (
                            <Button
                              key={next}
                              size="sm"
                              variant={claim.status === next ? "secondary" : "outline"}
                              disabled={statusMutation.isPending || claim.status === next}
                              onClick={() => statusMutation.mutate({ claimId: claim.id, nextStatus: next })}
                            >
                              {next}
                            </Button>
                          ))}
                          <Button size="sm" variant="ghost" asChild>
                            <Link to={`/claim-tracking/${claim.id}`}>Claim Detail <ChevronRight className="w-4 h-4 ml-1" /></Link>
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))
                )}
              </div>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center gap-2">
                <Bell className="w-5 h-5 text-primary" /> Unread Notifications
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {unread.length === 0 ? (
                <p className="text-sm text-muted-foreground">No unread notifications.</p>
              ) : (
                unread.slice(0, 8).map((n) => (
                  <div key={n.id} className="p-3 rounded-lg border border-border bg-secondary/30">
                    <p className="text-sm font-medium text-foreground">{n.title}</p>
                    <p className="text-xs text-muted-foreground mt-1">{n.message}</p>
                    <p className="text-xs text-muted-foreground mt-1">{timeAgo(n.created_at)}</p>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
