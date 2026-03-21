import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import Navbar from "@/components/landing/Navbar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";

export default function EligibilityDecision() {
  const navigate = useNavigate();
  const claimId = sessionStorage.getItem("activeClaimId") || "";

  const query = useQuery({
    queryKey: ["claim-eligibility", claimId],
    queryFn: () => api.claims.eligibility(claimId),
    enabled: Boolean(claimId),
  });

  const result = query.data;

  const goNext = () => {
    if (!result) return;
    if (result.next_action === "assisted") {
      navigate("/assisted-mode");
      return;
    }
    if (result.next_action === "chat") {
      navigate("/chat");
      return;
    }
    navigate("/dashboard");
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container pt-24 pb-16 px-4 max-w-2xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-display font-bold text-foreground">Eligibility pre-check</h1>
          <p className="text-sm text-muted-foreground mt-1">Policy and rule engine result before claim submission.</p>
        </div>

        <Card className="border-border bg-card">
          <CardHeader>
            <CardTitle className="text-base">Assessment</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="flex items-center gap-2">
              <span className="text-muted-foreground">Outcome:</span>
              <Badge variant="outline">{result?.outcome ?? "loading"}</Badge>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <div className="p-3 rounded-lg bg-secondary/40">
                <p className="text-muted-foreground">Has policy</p>
                <p className="font-medium text-foreground">{result?.coverage.has_policy ? "Yes" : "No"}</p>
              </div>
              <div className="p-3 rounded-lg bg-secondary/40">
                <p className="text-muted-foreground">Policy active</p>
                <p className="font-medium text-foreground">{result?.coverage.policy_active ? "Yes" : "No"}</p>
              </div>
              <div className="p-3 rounded-lg bg-secondary/40 sm:col-span-2">
                <p className="text-muted-foreground">Likely excluded</p>
                <p className="font-medium text-foreground">{result?.coverage.likely_excluded ? "Yes" : "No"}</p>
              </div>
            </div>
            <div>
              <p className="text-muted-foreground mb-1">Notes</p>
              <ul className="list-disc pl-5 space-y-1">
                {(result?.notes ?? []).map((n) => (
                  <li key={n} className="text-foreground">{n}</li>
                ))}
              </ul>
            </div>
          </CardContent>
        </Card>

        <div className="flex justify-between">
          <Button variant="outline" onClick={() => navigate("/incident-intake")}>Back</Button>
          <Button onClick={goNext} disabled={!result}>Continue</Button>
        </div>
      </main>
    </div>
  );
}
