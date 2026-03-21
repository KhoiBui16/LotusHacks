import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import Navbar from "@/components/landing/Navbar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

import { api } from "@/lib/api";

export default function AssistedMode() {
  const navigate = useNavigate();
  const claimId = sessionStorage.getItem("activeClaimId") || "";

  const [emergencyContacted, setEmergencyContacted] = useState(false);
  const [keptScene, setKeptScene] = useState(false);
  const [evidenceCollected, setEvidenceCollected] = useState(false);
  const [notes, setNotes] = useState("");

  const saveNotice = useMutation({
    mutationFn: async () => {
      if (!claimId) throw new Error("No active claim");
      await api.claims.firstNotice(claimId, {
        emergency_contacted: emergencyContacted,
        kept_scene: keptScene,
        initial_evidence_collected: evidenceCollected,
        notes,
      });
    },
    onSuccess: () => {
      navigate("/checklist-upload");
    },
  });

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container pt-24 pb-16 px-4 max-w-2xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-display font-bold text-foreground">Assisted mode</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Complex case detected. Capture first notice quickly, then continue with documents.
          </p>
        </div>

        <Card className="border-border bg-card">
          <CardHeader>
            <CardTitle className="text-base">Emergency guidance</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-muted-foreground">
            <p>1. Contact hotline or emergency services if injury exists.</p>
            <p>2. Keep scene safe and collect first evidence only.</p>
            <p>3. Continue with minimum info to avoid delays.</p>
            <div className="pt-2">
              <Button variant="outline" asChild>
                <a href="tel:1900xxxx">Call claims hotline</a>
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="border-border bg-card">
          <CardHeader>
            <CardTitle className="text-base">First notice</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center space-x-2">
              <Checkbox id="emergency" checked={emergencyContacted} onCheckedChange={(v) => setEmergencyContacted(v === true)} />
              <Label htmlFor="emergency">Emergency/hotline contacted</Label>
            </div>
            <div className="flex items-center space-x-2">
              <Checkbox id="scene" checked={keptScene} onCheckedChange={(v) => setKeptScene(v === true)} />
              <Label htmlFor="scene">Scene secured and preserved</Label>
            </div>
            <div className="flex items-center space-x-2">
              <Checkbox id="evidence" checked={evidenceCollected} onCheckedChange={(v) => setEvidenceCollected(v === true)} />
              <Label htmlFor="evidence">Initial evidence captured</Label>
            </div>
            <div className="space-y-2">
              <Label htmlFor="notes">Notes</Label>
              <Textarea id="notes" value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Any urgent context for insurer/human reviewer" />
            </div>
          </CardContent>
        </Card>

        <div className="flex justify-between">
          <Button variant="outline" onClick={() => navigate("/eligibility")}>Back</Button>
          <Button onClick={() => saveNotice.mutate()} disabled={!claimId || saveNotice.isPending}>Continue to documents</Button>
        </div>
      </main>
    </div>
  );
}
