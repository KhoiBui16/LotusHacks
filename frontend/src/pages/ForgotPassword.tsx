import { useState } from "react";
import { Link } from "react-router-dom";
import Navbar from "@/components/landing/Navbar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const { toast } = useToast();

  const submit = () => {
    toast({ title: "Request received", description: "If this email exists, reset instructions have been sent." });
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container pt-24 pb-16 px-4 max-w-md mx-auto space-y-6">
        <Card className="border-border bg-card">
          <CardHeader>
            <CardTitle>Forgot Password</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Email</Label>
              <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" />
            </div>
            <Button className="w-full" onClick={submit} disabled={!email.trim()}>Send reset instructions</Button>
            <Button variant="outline" className="w-full" asChild><Link to="/sign-in">Back to Sign In</Link></Button>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
