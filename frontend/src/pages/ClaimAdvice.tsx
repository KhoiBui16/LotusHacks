import { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Navbar from "@/components/landing/Navbar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import { api } from "@/lib/api";
import { ApiError } from "@/lib/apiClient";

function normalizeId(raw: string | null): string {
  const value = (raw ?? "").trim();
  if (!value || value === "undefined" || value === "null") return "";
  return /^[a-f\d]{24}$/i.test(value) ? value : "";
}

export default function ClaimAdvice() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const qc = useQueryClient();
  const activeClaimId = useMemo(() => normalizeId(sessionStorage.getItem("activeClaimId")), []);

  const eligibilityQuery = useQuery({
    queryKey: ["claim", activeClaimId, "eligibility"],
    queryFn: () => api.claims.eligibility(activeClaimId),
    enabled: Boolean(activeClaimId),
  });

  const adviceActionMutation = useMutation({
    mutationFn: (action: "save_draft" | "end_flow") => api.claims.adviceAction(activeClaimId, { action }),
    onSuccess: async (result) => {
      await Promise.all([
        qc.invalidateQueries({ queryKey: ["claim", activeClaimId] }),
        qc.invalidateQueries({ queryKey: ["claim", activeClaimId, "eligibility"] }),
        qc.invalidateQueries({ queryKey: ["claims"] }),
      ]);
      toast({
        title: result.status === "draft" ? "Draft saved" : "Claim closed",
        description: result.message,
      });
      navigate("/claims");
    },
    onError: (err) => {
      toast({
        title: "Unable to update claim",
        description: err instanceof Error ? err.message : "Please try again.",
        variant: "destructive",
      });
    },
  });

  if (!activeClaimId) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <main className="container pt-24 pb-16 px-4 max-w-3xl mx-auto">
          <Card>
            <CardHeader>
              <CardTitle>No active claim</CardTitle>
              <CardDescription>Start a claim first so we can load the pre-check advice.</CardDescription>
            </CardHeader>
            <CardContent>
              <Button onClick={() => navigate("/start-claim")}>Start claim</Button>
            </CardContent>
          </Card>
        </main>
      </div>
    );
  }

  if (eligibilityQuery.isLoading) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <main className="container pt-24 pb-16 px-4 max-w-3xl mx-auto">
          <Card>
            <CardHeader>
              <CardTitle>Loading advice</CardTitle>
              <CardDescription>We are fetching the latest pre-check result for this claim.</CardDescription>
            </CardHeader>
          </Card>
        </main>
      </div>
    );
  }

  if (eligibilityQuery.isError) {
    const error = eligibilityQuery.error as ApiError;
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <main className="container pt-24 pb-16 px-4 max-w-3xl mx-auto">
          <Card>
            <CardHeader>
              <CardTitle>Unable to load advice</CardTitle>
              <CardDescription>{error?.message || "Please try again."}</CardDescription>
            </CardHeader>
            <CardContent>
              <Button variant="outline" onClick={() => navigate("/incident-intake")}>
                Back to incident
              </Button>
            </CardContent>
          </Card>
        </main>
      </div>
    );
  }

  const eligibility = eligibilityQuery.data;
  const adviceText =
    eligibility?.advice_text ||
    eligibility?.notes?.[0] ||
    "The current pre-check does not support continuing this claim right now.";
  const recommendedActions =
    eligibility?.recommended_actions && eligibility.recommended_actions.length > 0
      ? eligibility.recommended_actions
      : ["Save this incident as a draft and review it again later."];

  if (eligibility && eligibility.next_action !== "exit") {
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <main className="container pt-24 pb-16 px-4 max-w-3xl mx-auto">
          <Card>
            <CardHeader>
              <CardTitle>This claim already has a next step</CardTitle>
              <CardDescription>
                The current eligibility result no longer points to the advice flow.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex gap-3">
              {eligibility.next_action === "chat" ? (
                <Button onClick={() => navigate("/chat")}>Go to chat</Button>
              ) : (
                <Button onClick={() => navigate("/assisted-mode")}>Go to assisted mode</Button>
              )}
              <Button variant="outline" onClick={() => navigate("/incident-intake")}>
                Back to incident
              </Button>
            </CardContent>
          </Card>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container pt-24 pb-16 px-4 max-w-3xl mx-auto">
        <Card>
          <CardHeader>
            <CardTitle>Claim advice</CardTitle>
            <CardDescription>
              The preliminary coverage check suggests you should review the options below before continuing.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                Recommendation
              </h2>
              <p className="text-base leading-7 text-foreground">{adviceText}</p>
            </div>

            <div className="space-y-2">
              <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                Suggested next actions
              </h2>
              <ul className="space-y-2 text-sm leading-6 text-foreground">
                {recommendedActions.map((action, index) => (
                  <li key={`${index}-${action}`} className="rounded-lg border border-border bg-muted/30 px-4 py-3">
                    {action}
                  </li>
                ))}
              </ul>
            </div>

            <div className="flex flex-col gap-3 sm:flex-row">
              <Button
                onClick={() => adviceActionMutation.mutate("save_draft")}
                disabled={adviceActionMutation.isPending}
              >
                Save draft
              </Button>
              <Button
                variant="outline"
                onClick={() => adviceActionMutation.mutate("end_flow")}
                disabled={adviceActionMutation.isPending}
              >
                End flow
              </Button>
              <Button variant="ghost" onClick={() => navigate("/incident-intake")}>
                Back to incident
              </Button>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
