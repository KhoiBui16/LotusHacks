import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useLanguage } from "@/contexts/LanguageContext";
import Navbar from "@/components/landing/Navbar";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Car, ShieldCheck, AlertTriangle, Upload, ArrowRight, CheckCircle2, ChevronLeft } from "lucide-react";
import { api } from "@/lib/api";
import { ApiError } from "@/lib/apiClient";
import { useAuth } from "@/contexts/AuthContext";

function claimIdOf(claim: unknown): string {
  const anyClaim = claim as { id?: string; _id?: string };
  return anyClaim?.id || anyClaim?._id || "";
}

export default function StartClaim() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { t } = useLanguage();
  const [selectedVehicle, setSelectedVehicle] = useState<string | null>(null);

  const vehiclesQuery = useQuery({
    queryKey: ["vehicles"],
    queryFn: api.vehicles.list,
  });

  const vehicles = useMemo(
    () =>
      (vehiclesQuery.data ?? []).map((v) => ({
        id: v.id,
        plate: v.plate || "—",
        model: `${v.model} ${v.year}`,
        policyLinked: Boolean(v.policy_linked),
        policyId: v.policy_id ?? null,
        insurer: v.insurer ?? null,
        expiry: v.expiry ?? null,
      })),
    [vehiclesQuery.data]
  );

  const vehicle = vehicles.find((v) => v.id === selectedVehicle);

  const createClaim = useMutation({
    mutationFn: () =>
      api.claims.create({
        vehicle_id: selectedVehicle as string,
        policy_id: vehicle?.policyId ?? undefined,
        insurer: vehicle?.insurer ?? undefined,
      }),
    onSuccess: (claim) => {
      const createdId = claimIdOf(claim);
      if (createdId) sessionStorage.setItem("activeClaimId", createdId);
      if (selectedVehicle) sessionStorage.setItem("activeVehicleId", selectedVehicle);
      if (vehicle?.policyLinked) {
        navigate("/incident-intake");
      } else {
        navigate("/policy-import");
      }
    },
  });

  useEffect(() => {
    if (user?.role === "admin") {
      navigate("/dashboard", { replace: true });
    }
  }, [navigate, user?.role]);

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container pt-24 pb-16 px-4 max-w-2xl mx-auto space-y-6">
        <Button variant="ghost" size="sm" asChild><Link to="/dashboard"><ChevronLeft className="w-4 h-4 mr-1" /> {t("sc.back")}</Link></Button>
        <div>
          <h1 className="text-2xl font-display font-bold text-foreground">{t("sc.title")}</h1>
          <p className="text-muted-foreground mt-1">{t("sc.subtitle")}</p>
        </div>
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">{t("sc.step1")}</h2>
          <div className="grid gap-3">
            {vehiclesQuery.isError && (vehiclesQuery.error as ApiError)?.status === 401 ? (
              <Card className="border-border bg-card">
                <CardContent className="py-6 text-sm text-muted-foreground">
                  Please sign in to continue.
                </CardContent>
              </Card>
            ) : null}

            {vehicles.map((v) => (
              <Card key={v.id} className={`cursor-pointer transition-all border-2 ${selectedVehicle === v.id ? "border-primary bg-primary/5" : "border-border hover:border-primary/40"}`} onClick={() => { setSelectedVehicle(v.id); sessionStorage.setItem("activeVehicleId", v.id); }}>
                <CardContent className="flex items-center justify-between py-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-secondary flex items-center justify-center"><Car className="w-5 h-5 text-primary" /></div>
                    <div>
                      <p className="font-display font-bold text-foreground">{v.plate}</p>
                      <p className="text-sm text-muted-foreground">{v.model}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {v.policyLinked ? (
                      <Badge variant="outline" className="border-primary/40 text-primary bg-primary/10 gap-1 text-xs"><ShieldCheck className="w-3 h-3" /> {t("sc.linked")}</Badge>
                    ) : (
                      <Badge variant="outline" className="border-yellow-500/40 text-yellow-400 bg-yellow-500/10 gap-1 text-xs"><AlertTriangle className="w-3 h-3" /> {t("sc.noPolicy")}</Badge>
                    )}
                    {selectedVehicle === v.id && <CheckCircle2 className="w-5 h-5 text-primary" />}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {vehicle && (
          <div className="space-y-3 animate-in fade-in slide-in-from-bottom-2 duration-300">
            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">{t("sc.step2")}</h2>
            {vehicle.policyLinked ? (
              <Card className="border-primary/30 bg-primary/5">
                <CardContent className="py-4 space-y-2">
                  <div className="flex items-center gap-2"><ShieldCheck className="w-5 h-5 text-primary" /><span className="font-semibold text-foreground">{t("sc.policyActive")}</span></div>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div><span className="text-muted-foreground">{t("sc.insurer")}</span> <span className="text-foreground">{vehicle.insurer}</span></div>
                    <div><span className="text-muted-foreground">{t("sc.policyId")}</span> <span className="text-foreground">{vehicle.policyId}</span></div>
                    <div><span className="text-muted-foreground">{t("sc.expiry")}</span> <span className="text-foreground">{vehicle.expiry}</span></div>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card className="border-yellow-500/30 bg-yellow-500/5">
                <CardContent className="py-4 space-y-3">
                  <div className="flex items-center gap-2"><AlertTriangle className="w-5 h-5 text-yellow-400" /><span className="font-semibold text-foreground">{t("sc.noPolicyLinked")}</span></div>
                  <p className="text-sm text-muted-foreground">{t("sc.noPolicyDesc")}</p>
                  <Button variant="outline" size="sm" onClick={() => createClaim.mutate()} disabled={createClaim.isPending}><Upload className="w-4 h-4 mr-1" /> {t("sc.importPolicy")}</Button>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {vehicle?.policyLinked && (
          <div className="pt-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
            <Button className="w-full" size="lg" onClick={() => createClaim.mutate()} disabled={createClaim.isPending}>
              {t("sc.continue")} <ArrowRight className="w-4 h-4 ml-1" />
            </Button>
          </div>
        )}
      </main>
    </div>
  );
}
