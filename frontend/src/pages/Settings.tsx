import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useLanguage } from "@/contexts/LanguageContext";
import Navbar from "@/components/landing/Navbar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ChevronLeft, Bell, Mail, Smartphone, MessageSquare, User, Shield, Globe, Save, CheckCircle2 } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { api } from "@/lib/api";
import { ApiError } from "@/lib/apiClient";

export default function Settings() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const { t, lang } = useLanguage();
  const [saved, setSaved] = useState(false);
  const [profile, setProfile] = useState({ fullName: "", email: "", phone: "" });
  const [userPasswordForm, setUserPasswordForm] = useState({ email: "", newPassword: "" });
  const [prefs, setPrefs] = useState({
    pushNotif: true, emailNotif: true, inAppNotif: true,
    claimUpdates: true, docReminders: true, marketingEmails: false,
    preferredContact: "email" as "email" | "phone" | "chat",
  });

  const meQuery = useQuery({ queryKey: ["me"], queryFn: api.me.get });
  const settingsQuery = useQuery({ queryKey: ["settings"], queryFn: api.settings.get });

  useEffect(() => {
    if (meQuery.data) {
      setProfile({
        fullName: meQuery.data.full_name ?? user?.name ?? "",
        email: meQuery.data.email ?? user?.email ?? "",
        phone: meQuery.data.phone ?? "",
      });
    }
  }, [meQuery.data, user?.email, user?.name]);

  useEffect(() => {
    if (settingsQuery.data) {
      setPrefs({
        pushNotif: Boolean(settingsQuery.data.push_notif),
        emailNotif: Boolean(settingsQuery.data.email_notif),
        inAppNotif: Boolean(settingsQuery.data.in_app_notif),
        claimUpdates: Boolean(settingsQuery.data.claim_updates),
        docReminders: Boolean(settingsQuery.data.doc_reminders),
        marketingEmails: Boolean(settingsQuery.data.marketing_emails),
        preferredContact: (settingsQuery.data.preferred_contact ?? "email") as "email" | "phone" | "chat",
      });
    }
  }, [settingsQuery.data]);

  const saveProfile = useMutation({
    mutationFn: () =>
      api.me.patch({
        full_name: profile.fullName,
        phone: profile.phone || undefined,
      }),
  });

  const saveSettings = useMutation({
    mutationFn: () =>
      api.settings.patch({
        push_notif: prefs.pushNotif,
        email_notif: prefs.emailNotif,
        in_app_notif: prefs.inAppNotif,
        claim_updates: prefs.claimUpdates,
        doc_reminders: prefs.docReminders,
        marketing_emails: prefs.marketingEmails,
        preferred_contact: prefs.preferredContact,
        language: lang,
      }),
  });

  const adminChangeUserPassword = useMutation({
    mutationFn: () =>
      api.admin.changeUserPassword({ email: userPasswordForm.email.trim(), new_password: userPasswordForm.newPassword }),
  });

  const handleSave = async () => {
    try {
      if (isAdmin) {
        await saveSettings.mutateAsync();
      } else {
        await Promise.all([saveProfile.mutateAsync(), saveSettings.mutateAsync()]);
      }
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch {
      void 0;
    }
  };
  const toggle = (key: keyof typeof prefs) => setPrefs((p) => ({ ...p, [key]: !p[key] }));

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container pt-24 pb-16 px-4 max-w-2xl mx-auto space-y-6">
        <Button variant="ghost" size="sm" asChild><Link to="/dashboard"><ChevronLeft className="w-4 h-4 mr-1" /> {t("ct.dashboard")}</Link></Button>
        <div>
          <h1 className="text-2xl font-display font-bold text-foreground">{t("set.title")}</h1>
          <p className="text-muted-foreground mt-1">{t("set.subtitle")}</p>
        </div>

        {!isAdmin && (
        <Card className="border-border bg-card">
          <CardHeader className="pb-2"><CardTitle className="text-base flex items-center gap-2"><User className="w-4 h-4 text-primary" /> {t("set.profile")}</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            {meQuery.isError && (meQuery.error as ApiError)?.status === 401 ? (
              <p className="text-sm text-muted-foreground">Please sign in to edit settings.</p>
            ) : null}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>{t("set.fullName")}</Label>
                <Input value={profile.fullName} onChange={(e) => setProfile((p) => ({ ...p, fullName: e.target.value }))} />
              </div>
              <div className="space-y-2">
                <Label>{t("set.email")}</Label>
                <Input value={profile.email} type="email" disabled />
              </div>
              <div className="space-y-2">
                <Label>{t("set.phone")}</Label>
                <Input value={profile.phone} onChange={(e) => setProfile((p) => ({ ...p, phone: e.target.value }))} type="tel" />
              </div>
              <div className="space-y-2">
                <Label>{t("set.language")}</Label>
                <div className="flex items-center gap-2">
                  <Globe className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm text-foreground">{lang === "en" ? "English" : "Tiếng Việt"}</span>
                  <Badge variant="outline" className="text-xs border-primary/30 text-primary">{t("set.default")}</Badge>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
        )}

        <Card className="border-border bg-card">
          <CardHeader className="pb-2"><CardTitle className="text-base flex items-center gap-2"><Bell className="w-4 h-4 text-primary" /> {t("set.notifChannels")}</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            {[
              { key: "pushNotif" as const, icon: Smartphone, label: t("set.push"), desc: t("set.pushDesc") },
              { key: "emailNotif" as const, icon: Mail, label: t("set.emailNotif"), desc: t("set.emailNotifDesc") },
              { key: "inAppNotif" as const, icon: Bell, label: t("set.inApp"), desc: t("set.inAppDesc") },
            ].map((item) => (
              <div key={item.key} className="flex items-center justify-between py-2">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg bg-secondary flex items-center justify-center"><item.icon className="w-4 h-4 text-muted-foreground" /></div>
                  <div><p className="text-sm font-medium text-foreground">{item.label}</p><p className="text-xs text-muted-foreground">{item.desc}</p></div>
                </div>
                <Switch checked={prefs[item.key] as boolean} onCheckedChange={() => toggle(item.key)} />
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className="border-border bg-card">
          <CardHeader className="pb-2"><CardTitle className="text-base flex items-center gap-2"><MessageSquare className="w-4 h-4 text-primary" /> {t("set.preferences")}</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            {[
              { key: "claimUpdates" as const, label: t("set.claimUpdates"), desc: t("set.claimUpdatesDesc") },
              { key: "docReminders" as const, label: t("set.docReminders"), desc: t("set.docRemindersDesc") },
              { key: "marketingEmails" as const, label: t("set.marketing"), desc: t("set.marketingDesc") },
            ].map((item) => (
              <div key={item.key} className="flex items-center justify-between py-2">
                <div><p className="text-sm font-medium text-foreground">{item.label}</p><p className="text-xs text-muted-foreground">{item.desc}</p></div>
                <Switch checked={prefs[item.key] as boolean} onCheckedChange={() => toggle(item.key)} />
              </div>
            ))}
            <div className="pt-2 border-t border-border">
              <Label className="text-sm font-medium">{t("set.preferredContact")}</Label>
              <div className="flex gap-2 mt-2">
                {(["email", "phone", "chat"] as const).map((ch) => (
                  <Button key={ch} variant={prefs.preferredContact === ch ? "default" : "outline"} size="sm" onClick={() => setPrefs((p) => ({ ...p, preferredContact: ch }))} className="capitalize">{ch}</Button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-border bg-card">
          <CardHeader className="pb-2"><CardTitle className="text-base flex items-center gap-2"><Shield className="w-4 h-4 text-primary" /> {t("set.security")}</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <Button variant="outline" size="sm" asChild><Link to="/change-password">{t("set.changePassword")}</Link></Button>
            <p className="text-xs text-muted-foreground">{t("set.lastPasswordChange")}</p>
          </CardContent>
        </Card>

        {isAdmin && (
          <Card className="border-border bg-card">
            <CardHeader className="pb-2"><CardTitle className="text-base flex items-center gap-2"><Shield className="w-4 h-4 text-primary" /> Admin: Change User Password</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              <div className="space-y-2">
                <Label>User Email</Label>
                <Input value={userPasswordForm.email} onChange={(e) => setUserPasswordForm((p) => ({ ...p, email: e.target.value }))} type="email" placeholder="user@example.com" />
              </div>
              <div className="space-y-2">
                <Label>New Password</Label>
                <Input value={userPasswordForm.newPassword} onChange={(e) => setUserPasswordForm((p) => ({ ...p, newPassword: e.target.value }))} type="password" minLength={8} placeholder="At least 8 characters" />
              </div>
              <div className="flex justify-end">
                <Button
                  onClick={async () => {
                    try {
                      await adminChangeUserPassword.mutateAsync();
                      setUserPasswordForm({ email: "", newPassword: "" });
                      setSaved(true);
                      setTimeout(() => setSaved(false), 2000);
                    } catch {
                      void 0;
                    }
                  }}
                  disabled={adminChangeUserPassword.isPending || !userPasswordForm.email.trim() || userPasswordForm.newPassword.length < 8}
                >
                  Change User Password
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        <div className="flex justify-end pt-2">
          <Button onClick={handleSave} size="lg" disabled={saveProfile.isPending || saveSettings.isPending}>
            {saved ? <><CheckCircle2 className="w-4 h-4 mr-1" /> {t("set.saved")}</> : <><Save className="w-4 h-4 mr-1" /> {t("set.saveChanges")}</>}
          </Button>
        </div>
      </main>
    </div>
  );
}
