import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useLanguage } from "@/contexts/LanguageContext";
import Navbar from "@/components/landing/Navbar";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Bell, ChevronLeft, CheckCircle2, AlertTriangle, Clock, ChevronRight, Check } from "lucide-react";
import { api } from "@/lib/api";
import { ApiError } from "@/lib/apiClient";

interface NotificationItem {
  id: string;
  type: "status" | "docs" | "decision" | "info";
  title: string;
  message: string;
  created_at: string;
  read: boolean;
  claim_id?: string | null;
}

function timeAgo(iso: string) {
  const ms = Date.now() - new Date(iso).getTime();
  const mins = Math.max(0, Math.floor(ms / 60000));
  if (mins < 60) return `${mins} min ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} hours ago`;
  const days = Math.floor(hours / 24);
  return `${days} days ago`;
}

const typeConfig: Record<string, { icon: React.ElementType; color: string }> = {
  status: { icon: Clock, color: "text-yellow-400 bg-yellow-500/15" },
  docs: { icon: AlertTriangle, color: "text-orange-400 bg-orange-500/15" },
  decision: { icon: CheckCircle2, color: "text-primary bg-primary/15" },
  info: { icon: Bell, color: "text-muted-foreground bg-secondary" },
};

export default function Notifications() {
  const { t } = useLanguage();
  const [tab, setTab] = useState("all");
  const qc = useQueryClient();

  const notificationsQuery = useQuery({
    queryKey: ["notifications", tab],
    queryFn: () => api.notifications.list(tab === "unread" ? "unread" : "all"),
  });

  const notifications = (notificationsQuery.data ?? []) as NotificationItem[];
  const unreadCount = useMemo(() => notifications.filter((n) => !n.read).length, [notifications]);

  const markAllRead = useMutation({
    mutationFn: api.notifications.readAll,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  const markRead = useMutation({
    mutationFn: (id: string) => api.notifications.read(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container pt-24 pb-16 px-4 max-w-2xl mx-auto space-y-6">
        <Button variant="ghost" size="sm" asChild><Link to="/dashboard"><ChevronLeft className="w-4 h-4 mr-1" /> {t("ct.dashboard")}</Link></Button>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-display font-bold text-foreground">{t("notif.title")}</h1>
            <p className="text-muted-foreground mt-1">{unreadCount > 0 ? `${unreadCount} ${t("notif.unread")}` : t("notif.allCaughtUp")}</p>
          </div>
          {unreadCount > 0 && <Button variant="outline" size="sm" onClick={() => markAllRead.mutate()}><Check className="w-3 h-3 mr-1" /> {t("notif.markAllRead")}</Button>}
        </div>

        <Tabs value={tab} onValueChange={setTab}>
          <TabsList className="w-full max-w-xs grid grid-cols-2">
            <TabsTrigger value="all">{t("notif.all")}</TabsTrigger>
            <TabsTrigger value="unread">{t("notif.unreadTab")} {unreadCount > 0 && <Badge className="ml-1.5 h-5 w-5 p-0 flex items-center justify-center text-[10px]">{unreadCount}</Badge>}</TabsTrigger>
          </TabsList>
          <TabsContent value={tab} className="mt-4 space-y-3">
            {notificationsQuery.isError && (notificationsQuery.error as ApiError)?.status === 401 ? (
              <Card className="border-border bg-card">
                <CardContent className="py-12 text-center">
                  <p className="text-sm text-muted-foreground">Please sign in to view notifications.</p>
                </CardContent>
              </Card>
            ) : null}

            {notifications.length === 0 ? (
              <Card className="border-border bg-card"><CardContent className="py-12 text-center"><Bell className="w-10 h-10 text-muted-foreground mx-auto mb-3" /><p className="text-sm text-muted-foreground">{tab === "unread" ? t("notif.noUnread") : t("notif.noNotifications")}</p></CardContent></Card>
            ) : (
              notifications.map((n) => {
                const tc = typeConfig[n.type];
                const Icon = tc.icon;
                return (
                  <Card key={n.id} className={`border transition-all cursor-pointer hover:bg-secondary/30 ${!n.read ? "border-primary/20 bg-primary/5" : "border-border bg-card"}`} onClick={() => markRead.mutate(n.id)}>
                    <CardContent className="py-4 flex items-start gap-3">
                      <div className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${tc.color}`}><Icon className="w-4 h-4" /></div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className={`text-sm font-medium ${!n.read ? "text-foreground" : "text-muted-foreground"}`}>{n.title}</p>
                          {!n.read && <div className="w-2 h-2 rounded-full bg-primary shrink-0" />}
                        </div>
                        <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">{n.message}</p>
                        <p className="text-[11px] text-muted-foreground/60 mt-1">{timeAgo(n.created_at)}</p>
                      </div>
                      {n.claim_id && (
                        <Link to={`/claim-tracking/${n.claim_id}`} className="shrink-0" onClick={(e) => e.stopPropagation()}>
                          <Badge variant="outline" className="text-xs border-border hover:border-primary/40 transition-colors">{String(n.claim_id).slice(-6)} <ChevronRight className="w-3 h-3 ml-0.5" /></Badge>
                        </Link>
                      )}
                    </CardContent>
                  </Card>
                );
              })
            )}
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
