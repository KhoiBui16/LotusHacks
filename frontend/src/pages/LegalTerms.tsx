import { Link } from "react-router-dom";
import Navbar from "@/components/landing/Navbar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function LegalTerms() {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container pt-24 pb-16 px-4 max-w-3xl mx-auto space-y-6">
        <h1 className="text-2xl font-display font-bold text-foreground">Terms & Conditions</h1>
        <Card className="border-border bg-card">
          <CardHeader>
            <CardTitle>Claim Submission Terms</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground space-y-3 leading-relaxed">
            <p>You confirm information provided for claims is accurate and complete.</p>
            <p>You agree insurer may request additional documents and perform verification checks.</p>
            <p>False or misleading information may lead to claim rejection based on policy conditions.</p>
          </CardContent>
        </Card>
        <Button asChild><Link to="/review-submit">Back to Review</Link></Button>
      </main>
    </div>
  );
}
