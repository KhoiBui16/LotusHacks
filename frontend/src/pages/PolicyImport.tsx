import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import Navbar from "@/components/landing/Navbar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

function normalizeId(raw: string | null): string {
  const v = (raw ?? "").trim();
  if (!v || v === "undefined" || v === "null") return "";
  return /^[a-f\d]{24}$/i.test(v) ? v : "";
}

function claimIdOf(claim: unknown): string {
  const anyClaim = claim as { id?: string; _id?: string };
  const raw = anyClaim?.id || anyClaim?._id || "";
  return normalizeId(raw);
}

export default function PolicyImport() {
  const navigate = useNavigate();
  const { toast } = useToast();

  const [policyId, setPolicyId] = useState("");
  const [insurer, setInsurer] = useState("");
  const [effectiveDate, setEffectiveDate] = useState("");
  const [expiry, setExpiry] = useState("");

  const submit = useMutation({
    mutationFn: async () => {
      let claimId = normalizeId(sessionStorage.getItem("activeClaimId"));
      if (!claimId) {
        const activeVehicleId = normalizeId(sessionStorage.getItem("activeVehicleId"));
        if (!activeVehicleId) {
          throw new Error("No active vehicle/claim. Please choose a vehicle first.");
        }
        const created = await api.claims.create({ vehicle_id: activeVehicleId });
        claimId = claimIdOf(created);
        if (!claimId) throw new Error("Failed to create claim id");
        sessionStorage.setItem("activeClaimId", claimId);
      }

      await api.claims.policyImport(claimId, {
        policy_id: policyId,
        insurer,
        effective_date: effectiveDate || undefined,
        expiry: expiry || undefined,
        source: "manual",
      });

      const claim = await api.claims.get(claimId);
      await api.vehicles.linkPolicy(claim.vehicle_id, {
        policy_id: policyId,
        insurer,
        effective_date: effectiveDate || undefined,
        expiry: expiry || undefined,
      });
    },
    onSuccess: () => {
      toast({ title: "Policy imported", description: "Policy has been linked to your vehicle." });
      navigate("/incident-intake");
    },
    onError: (err) => {
      toast({
        title: "Import policy failed",
        description: err instanceof Error ? err.message : "Please try again.",
        variant: "destructive",
      });
    },
  });

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container pt-24 pb-16 px-4 max-w-xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-display font-bold text-foreground">Import policy</h1>
          <p className="text-sm text-muted-foreground mt-1">
            No linked policy found for this vehicle. Add policy details to continue the claim flow.
          </p>
        </div>

        <Card className="border-border bg-card">
          <CardHeader>
            <CardTitle className="text-base">Policy details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="policy-id">Policy number</Label>
              <Input id="policy-id" value={policyId} onChange={(e) => setPolicyId(e.target.value)} placeholder="POL-2026-0001" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="insurer">Insurer</Label>
              <Input id="insurer" value={insurer} onChange={(e) => setInsurer(e.target.value)} placeholder="Bao Viet" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label htmlFor="effective">Effective date</Label>
                <Input id="effective" type="date" value={effectiveDate} onChange={(e) => setEffectiveDate(e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="expiry">Expiry date</Label>
                <Input id="expiry" type="date" value={expiry} onChange={(e) => setExpiry(e.target.value)} />
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="flex justify-between">
          <Button variant="outline" onClick={() => navigate("/start-claim")}>Back</Button>
          <Button
            onClick={() => submit.mutate()}
            disabled={!policyId.trim() || !insurer.trim() || submit.isPending}
          >
            Continue to intake
          </Button>
        </div>
      </main>
    </div>
  );
}
