import { Link, useLocation } from "react-router-dom";
import Navbar from "@/components/landing/Navbar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const docsByTopic: Record<string, { title: string; bullets: string[] }> = {
  rfid: {
    title: "RFID Infrastructure Docs",
    bullets: ["Tag enrollment and provisioning", "Lane reader calibration checklist", "Failure and fallback handling"],
  },
  security: {
    title: "Security & Compliance Docs",
    bullets: ["Encryption and key rotation", "Audit logging requirements", "Fraud signal pipeline"],
  },
  processing: {
    title: "Edge Processing Docs",
    bullets: ["Low-latency event ingestion", "Retry and idempotency", "Operational runbooks"],
  },
  analytics: {
    title: "Analytics & Intelligence Docs",
    bullets: ["Data model and dimensions", "Realtime dashboard metrics", "Forecasting caveats"],
  },
  integration: {
    title: "Open Integration Docs",
    bullets: ["Public API reference", "Webhook verification", "Partner SDK quickstart"],
  },
};

export default function DocsCenter() {
  const { search } = useLocation();
  const topic = new URLSearchParams(search).get("topic") || "integration";
  const doc = docsByTopic[topic] ?? docsByTopic.integration;

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container pt-24 pb-16 px-4 max-w-3xl mx-auto space-y-6">
        <h1 className="text-2xl font-display font-bold text-foreground">Documentation Center</h1>
        <Card className="border-border bg-card">
          <CardHeader>
            <CardTitle>{doc.title}</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="list-disc pl-5 space-y-2 text-sm text-muted-foreground">
              {doc.bullets.map((b) => (
                <li key={b}>{b}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
        <div className="flex gap-2">
          <Button variant="outline" asChild><Link to="/core-services">Back to Core Services</Link></Button>
          <Button asChild><Link to="/dashboard">Open Dashboard</Link></Button>
        </div>
      </main>
    </div>
  );
}
