import { useState } from "react";
import { Link } from "react-router-dom";
import { useLanguage } from "@/contexts/LanguageContext";
import Navbar from "@/components/landing/Navbar";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Bell, ChevronLeft, CheckCircle2, AlertTriangle, Clock, ChevronRight, Check } from "lucide-react";

interface Notification {
  id: number; type: "status" | "docs" | "decision" | "info"; title: string; titleVi: string;
  message: string; messageVi: string; time: string; timeVi: string; read: boolean; claimId?: string;
}

const mockNotifications: Notification[] = [
  { id: 1, type: "docs", title: "Documents Required", titleVi: "Cần bổ sung tài liệu", message: "CLM-004 requires a repair estimate from your garage. Due by Dec 25.", messageVi: "CLM-004 cần bảng ước tính sửa chữa từ garage. Hạn: 25/12.", time: "2 hours ago", timeVi: "2 giờ trước", read: false, claimId: "CLM-004" },
  { id: 2, type: "status", title: "Status Updated", titleVi: "Cập nhật trạng thái", message: "CLM-004 is now under insurer review.", messageVi: "CLM-004 đang được bảo hiểm xem xét.", time: "5 hours ago", timeVi: "5 giờ trước", read: false, claimId: "CLM-004" },
  { id: 3, type: "decision", title: "Claim Approved", titleVi: "Hồ sơ được duyệt", message: "CLM-002 has been approved. Settlement: 8,500,000 VND.", messageVi: "CLM-002 đã được duyệt. Bồi thường: 8.500.000 VND.", time: "1 day ago", timeVi: "1 ngày trước", read: true, claimId: "CLM-002" },
  { id: 4, type: "status", title: "Documents Verified", titleVi: "Tài liệu đã xác minh", message: "All documents for CLM-004 have been verified.", messageVi: "Tất cả tài liệu CLM-004 đã được xác minh.", time: "1 day ago", timeVi: "1 ngày trước", read: true, claimId: "CLM-004" },
  { id: 5, type: "info", title: "Welcome to VETC Claims", titleVi: "Chào mừng đến VETC Claims", message: "Your account has been set up successfully.", messageVi: "Tài khoản đã được thiết lập thành công.", time: "3 days ago", timeVi: "3 ngày trước", read: true },
  { id: 6, type: "decision", title: "Claim Rejected", titleVi: "Hồ sơ bị từ chối", message: "CLM-005 was rejected. Reason: Flood damage exclusion.", messageVi: "CLM-005 bị từ chối. Lý do: Loại trừ thiệt hại ngập nước.", time: "5 days ago", timeVi: "5 ngày trước", read: true, claimId: "CLM-005" },
];

const typeConfig: Record<string, { icon: React.ElementType; color: string }> = {
  status: { icon: Clock, color: "text-yellow-400 bg-yellow-500/15" },
  docs: { icon: AlertTriangle, color: "text-orange-400 bg-orange-500/15" },
  decision: { icon: CheckCircle2, color: "text-primary bg-primary/15" },
  info: { icon: Bell, color: "text-muted-foreground bg-secondary" },
};

export default function Notifications() {
  const { t, lang } = useLanguage();
  const [tab, setTab] = useState("all");
  const [notifications, setNotifications] = useState(mockNotifications);
  const unreadCount = notifications.filter((n) => !n.read).length;
  const filtered = tab === "all" ? notifications : notifications.filter((n) => !n.read);

  const markAllRead = () => setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  const markRead = (id: number) => setNotifications((prev) => prev.map((n) => n.id === id ? { ...n, read: true } : n));

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
          {unreadCount > 0 && <Button variant="outline" size="sm" onClick={markAllRead}><Check className="w-3 h-3 mr-1" /> {t("notif.markAllRead")}</Button>}
        </div>

        <Tabs value={tab} onValueChange={setTab}>
          <TabsList className="w-full max-w-xs grid grid-cols-2">
            <TabsTrigger value="all">{t("notif.all")}</TabsTrigger>
            <TabsTrigger value="unread">{t("notif.unreadTab")} {unreadCount > 0 && <Badge className="ml-1.5 h-5 w-5 p-0 flex items-center justify-center text-[10px]">{unreadCount}</Badge>}</TabsTrigger>
          </TabsList>
          <TabsContent value={tab} className="mt-4 space-y-3">
            {filtered.length === 0 ? (
              <Card className="border-border bg-card"><CardContent className="py-12 text-center"><Bell className="w-10 h-10 text-muted-foreground mx-auto mb-3" /><p className="text-sm text-muted-foreground">{tab === "unread" ? t("notif.noUnread") : t("notif.noNotifications")}</p></CardContent></Card>
            ) : (
              filtered.map((n) => {
                const tc = typeConfig[n.type];
                const Icon = tc.icon;
                return (
                  <Card key={n.id} className={`border transition-all cursor-pointer hover:bg-secondary/30 ${!n.read ? "border-primary/20 bg-primary/5" : "border-border bg-card"}`} onClick={() => markRead(n.id)}>
                    <CardContent className="py-4 flex items-start gap-3">
                      <div className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${tc.color}`}><Icon className="w-4 h-4" /></div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className={`text-sm font-medium ${!n.read ? "text-foreground" : "text-muted-foreground"}`}>{lang === "vi" ? n.titleVi : n.title}</p>
                          {!n.read && <div className="w-2 h-2 rounded-full bg-primary shrink-0" />}
                        </div>
                        <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">{lang === "vi" ? n.messageVi : n.message}</p>
                        <p className="text-[11px] text-muted-foreground/60 mt-1">{lang === "vi" ? n.timeVi : n.time}</p>
                      </div>
                      {n.claimId && (
                        <Link to={`/claim-tracking/${n.claimId}`} className="shrink-0" onClick={(e) => e.stopPropagation()}>
                          <Badge variant="outline" className="text-xs border-border hover:border-primary/40 transition-colors">{n.claimId} <ChevronRight className="w-3 h-3 ml-0.5" /></Badge>
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
