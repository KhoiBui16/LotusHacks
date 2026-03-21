import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import Navbar from "@/components/landing/Navbar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/hooks/use-toast";
import { api } from "@/lib/api";

export default function ClaimAppeal() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [reason, setReason] = useState("");

  const mutation = useMutation({
    mutationFn: () => api.claims.appeal(id || "", { reason }),
    onSuccess: () => {
      toast({ title: "Appeal submitted", description: "Your appeal is now under review." });
      navigate(`/claim-tracking/${id}`);
    },
    onError: (err) => {
      toast({ title: "Appeal failed", description: err instanceof Error ? err.message : "Please try again.", variant: "destructive" });
    },
  });

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container pt-24 pb-16 px-4 max-w-2xl mx-auto space-y-6">
        <h1 className="text-2xl font-display font-bold text-foreground">Appeal Claim Decision</h1>
        <Card className="border-border bg-card">
          <CardHeader>
            <CardTitle>Appeal reason</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Textarea rows={6} value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Explain why you disagree with this claim decision..." />
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => navigate(`/claim-tracking/${id}`)}>Cancel</Button>
              <Button onClick={() => mutation.mutate()} disabled={mutation.isPending || reason.trim().length < 5}>Submit Appeal</Button>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
