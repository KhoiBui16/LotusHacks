import { Link } from "react-router-dom";
import { useLanguage } from "@/contexts/LanguageContext";
import Navbar from "@/components/landing/Navbar";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { AlertTriangle, Phone, Camera, MessageSquare, ArrowRight, Shield } from "lucide-react";

export default function Emergency() {
  const { t } = useLanguage();
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container pt-24 pb-16 px-4 max-w-2xl mx-auto space-y-6">
        <Card className="border-2 border-destructive/50 bg-destructive/10">
          <CardContent className="py-6 flex flex-col items-center text-center gap-3">
            <div className="w-16 h-16 rounded-full bg-destructive/20 flex items-center justify-center animate-pulse"><AlertTriangle className="w-8 h-8 text-destructive" /></div>
            <h1 className="text-2xl font-display font-bold text-foreground">{t("em.title")}</h1>
            <p className="text-muted-foreground max-w-md">{t("em.subtitle")}</p>
          </CardContent>
        </Card>

        <div className="space-y-4">
          <h2 className="text-lg font-display font-semibold text-foreground">{t("em.immediateActions")}</h2>
          {[
            { icon: Phone, title: t("em.callEmergency"), desc: t("em.callEmergencyDesc"), cta: t("em.call113"), color: "destructive" },
            { icon: Shield, title: t("em.secureScene"), desc: t("em.secureSceneDesc"), cta: null, color: "primary" },
            { icon: Camera, title: t("em.documentAll"), desc: t("em.documentAllDesc"), cta: null, color: "primary" },
          ].map((item, i) => (
            <Card key={i} className="border-border bg-card">
              <CardContent className="py-4 flex items-start gap-4">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${item.color === "destructive" ? "bg-destructive/20" : "bg-primary/20"}`}>
                  <item.icon className={`w-5 h-5 ${item.color === "destructive" ? "text-destructive" : "text-primary"}`} />
                </div>
                <div className="flex-1 space-y-1">
                  <h3 className="font-semibold text-foreground">{item.title}</h3>
                  <p className="text-sm text-muted-foreground">{item.desc}</p>
                  {item.cta && <Button variant="destructive" size="sm" className="mt-2" asChild><a href="tel:113"><Phone className="w-3 h-3 mr-1" />{item.cta}</a></Button>}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        <Card className="border-primary/30 bg-primary/5">
          <CardContent className="py-5 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <MessageSquare className="w-6 h-6 text-primary" />
              <div>
                <p className="font-semibold text-foreground">{t("em.hotline")}</p>
                <p className="text-sm text-muted-foreground">{t("em.hotlineDesc")}</p>
              </div>
            </div>
            <Button variant="outline" asChild><a href="tel:1900xxxx"><Phone className="w-4 h-4 mr-1" /> 1900-XXXX</a></Button>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-4">
          <Button variant="outline" className="h-auto py-4" asChild>
            <Link to="/checklist-upload">{t("em.continueMinimum")} <ArrowRight className="w-4 h-4 ml-1" /></Link>
          </Button>
          <Button className="h-auto py-4" asChild>
            <a href="tel:1900xxxx"><Phone className="w-4 h-4 mr-1" /> {t("em.contactSupport")}</a>
          </Button>
        </div>
      </main>
    </div>
  );
}
