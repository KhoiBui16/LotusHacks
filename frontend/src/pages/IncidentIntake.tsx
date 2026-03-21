import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useLanguage } from "@/contexts/LanguageContext";
import { useToast } from "@/hooks/use-toast";
import Navbar from "@/components/landing/Navbar";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Car, Droplets, ShieldAlert, Glasses, ParkingMeter, HelpCircle,
  ChevronLeft, ChevronRight, Check, MapPin, Clock, FileText, Users, Heart
} from "lucide-react";
import { TranslationKey } from "@/i18n/translations";
import { api } from "@/lib/api";
import type { Claim } from "@/lib/api";

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

const INCIDENT_DRAFT_KEY = "incident_intake_draft";

type IncidentIntakeData = {
  type: string;
  date: string;
  time: string;
  location: string;
  description: string;
  hasThirdParty: boolean | null;
  thirdPartyInfo: string;
  canDrive: boolean | null;
  needsTowing: boolean | null;
  hasInjury: boolean | null;
};

const initialIncidentData: IncidentIntakeData = {
  type: "",
  date: "",
  time: "",
  location: "",
  description: "",
  hasThirdParty: null,
  thirdPartyInfo: "",
  canDrive: null,
  needsTowing: null,
  hasInjury: null,
};

export default function IncidentIntake() {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const { toast } = useToast();

  const STEPS = [
    { id: "type", label: t("ii.stepType"), icon: ShieldAlert },
    { id: "time", label: t("ii.stepTime"), icon: Clock },
    { id: "location", label: t("ii.stepLocation"), icon: MapPin },
    { id: "description", label: t("ii.stepDesc"), icon: FileText },
    { id: "third-party", label: t("ii.stepThirdParty"), icon: Users },
    { id: "vehicle-condition", label: t("ii.stepVehicle"), icon: Car },
    { id: "injury", label: t("ii.stepInjury"), icon: Heart },
  ];

  const incidentTypes: { id: string; labelKey: TranslationKey; icon: typeof Car }[] = [
    { id: "collision", labelKey: "ii.collision", icon: Car },
    { id: "scratch", labelKey: "ii.scratch", icon: ParkingMeter },
    { id: "glass", labelKey: "ii.glass", icon: Glasses },
    { id: "flood", labelKey: "ii.flood", icon: Droplets },
    { id: "theft", labelKey: "ii.theft", icon: ShieldAlert },
    { id: "other", labelKey: "ii.other", icon: HelpCircle },
  ];

  const [step, setStep] = useState(0);
  const activeClaimId = normalizeId(sessionStorage.getItem("activeClaimId"));
  const restoredRef = useRef(false);
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<any>(null);
  const markerRef = useRef<any>(null);
  const mapsListenersRef = useRef<any[]>([]);
  const [mapReady, setMapReady] = useState(false);
  const [mapError, setMapError] = useState<string>("");
  const googleMapsApiKey = useMemo(() => {
    const v = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;
    return v && v.trim() ? v.trim() : "";
  }, []);
  const [data, setData] = useState<IncidentIntakeData>(initialIncidentData);

  const claimQuery = useQuery<Claim>({
    queryKey: ["claim", activeClaimId, "incident-intake"],
    queryFn: () => api.claims.get(activeClaimId),
    enabled: Boolean(activeClaimId),
  });

  useEffect(() => {
    if (restoredRef.current) return;
    const raw = sessionStorage.getItem(INCIDENT_DRAFT_KEY);
    if (!raw) return;
    try {
      const parsed = JSON.parse(raw) as {
        claimId?: string;
        step?: number;
        data?: Partial<IncidentIntakeData>;
      };
      const draftClaimId = normalizeId(parsed.claimId ?? "");
      if (activeClaimId && draftClaimId && activeClaimId !== draftClaimId) return;
      if (parsed.data) {
        setData((prev) => ({ ...prev, ...parsed.data }));
      }
      if (typeof parsed.step === "number" && parsed.step >= 0 && parsed.step <= 6) {
        setStep(parsed.step);
      }
      restoredRef.current = true;
    } catch {
      void 0;
    }
  }, [activeClaimId]);

  useEffect(() => {
    if (!activeClaimId || restoredRef.current) return;
    const incident = claimQuery.data?.incident;
    if (!incident) return;
    setData({
      type: incident.type,
      date: incident.date,
      time: incident.time || "",
      location: incident.location_text,
      description: incident.description || "",
      hasThirdParty: incident.has_third_party,
      thirdPartyInfo: incident.third_party_info || "",
      canDrive: incident.can_drive,
      needsTowing: incident.needs_towing,
      hasInjury: incident.has_injury,
    });
    setStep(6);
    restoredRef.current = true;
  }, [activeClaimId, claimQuery.data?.incident]);

  useEffect(() => {
    sessionStorage.setItem(
      INCIDENT_DRAFT_KEY,
      JSON.stringify({
        claimId: activeClaimId || null,
        step,
        data,
      })
    );
  }, [activeClaimId, data, step]);

  const useCurrentLocation = () => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition((pos) => {
      const { latitude, longitude } = pos.coords;
      setData((prev) => ({ ...prev, location: `${latitude.toFixed(6)}, ${longitude.toFixed(6)}` }));
      if (mapRef.current && markerRef.current) {
        const next = { lat: latitude, lng: longitude };
        markerRef.current.setPosition(next);
        mapRef.current.panTo(next);
        mapRef.current.setZoom(16);
      }
    });
  };

  useEffect(() => {
    if (step !== 2) return;
    if (!googleMapsApiKey) {
      setMapError("Google Maps key is missing");
      return;
    }
    if (!mapContainerRef.current) return;

    const initMap = () => {
      if (!window.google?.maps || !mapContainerRef.current) {
        setMapError("Google Maps failed to initialize");
        return;
      }

      const initialCenter = { lat: 10.7769, lng: 106.7009 };
      mapRef.current = new window.google.maps.Map(mapContainerRef.current, {
        center: initialCenter,
        zoom: 13,
        mapTypeControl: false,
        streetViewControl: false,
        fullscreenControl: false,
      });
      markerRef.current = new window.google.maps.Marker({
        position: initialCenter,
        map: mapRef.current,
        draggable: true,
        title: "Selected location",
      });

      mapsListenersRef.current.push(
        mapRef.current.addListener("click", (ev: any) => {
          const lat = ev.latLng.lat();
          const lng = ev.latLng.lng();
          markerRef.current.setPosition({ lat, lng });
          setData((prev) => ({ ...prev, location: `${lat.toFixed(6)}, ${lng.toFixed(6)}` }));
        })
      );

      mapsListenersRef.current.push(
        markerRef.current.addListener("dragend", (ev: any) => {
          const lat = ev.latLng.lat();
          const lng = ev.latLng.lng();
          setData((prev) => ({ ...prev, location: `${lat.toFixed(6)}, ${lng.toFixed(6)}` }));
        })
      );

      setMapReady(true);
      setMapError("");
    };

    if (window.google?.maps) {
      initMap();
      return;
    }

    const src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(googleMapsApiKey)}`;
    const existing = document.querySelector<HTMLScriptElement>(`script[src="${src}"]`);
    if (existing) {
      existing.addEventListener("load", initMap, { once: true });
      return;
    }

    const script = document.createElement("script");
    script.src = src;
    script.async = true;
    script.defer = true;
    script.onload = initMap;
    script.onerror = () => setMapError("Failed to load Google Maps script");
    document.head.appendChild(script);

    return () => {
      mapsListenersRef.current.forEach((l) => {
        if (l && typeof l.remove === "function") l.remove();
      });
      mapsListenersRef.current = [];
    };
  }, [step, googleMapsApiKey]);

  useEffect(() => {
    if (!mapReady || !mapRef.current || !markerRef.current) return;
    const m = data.location.match(/(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)/);
    if (!m) return;
    const lat = Number(m[1]);
    const lng = Number(m[2]);
    if (!Number.isFinite(lat) || !Number.isFinite(lng)) return;
    markerRef.current.setPosition({ lat, lng });
    mapRef.current.panTo({ lat, lng });
  }, [data.location, mapReady]);

  const currentStep = STEPS[step];
  const progressPercent = ((step + 1) / STEPS.length) * 100;
  const canNext = () => {
    switch (step) {
      case 0: return !!data.type;
      case 1: return !!data.date;
      case 2: return !!data.location;
      case 3: return !!data.description;
      case 4: return data.hasThirdParty !== null;
      case 5: return data.canDrive !== null;
      case 6: return data.hasInjury !== null;
      default: return true;
    }
  };

  const handleNext = () => {
    if (step < STEPS.length - 1) setStep(step + 1);
    else finish.mutate();
  };

  const finish = useMutation({
    mutationFn: async () => {
      let claimId = normalizeId(sessionStorage.getItem("activeClaimId"));
      if (!claimId) {
        const activeVehicleId = normalizeId(sessionStorage.getItem("activeVehicleId"));
        if (!activeVehicleId) {
          throw new Error("No active claim/vehicle. Please start claim flow again.");
        }
        const created = await api.claims.create({ vehicle_id: activeVehicleId });
        claimId = claimIdOf(created);
        if (!claimId) throw new Error("Could not initialize claim");
        sessionStorage.setItem("activeClaimId", claimId);
      }

      await api.claims.patch(claimId, {
        incident: {
          type: data.type,
          date: data.date,
          time: data.time || null,
          location_text: data.location,
          description: data.description || null,
          has_third_party: Boolean(data.hasThirdParty),
          third_party_info: data.hasThirdParty ? data.thirdPartyInfo || null : null,
          can_drive: data.canDrive ?? true,
          needs_towing: data.needsTowing ?? false,
          has_injury: Boolean(data.hasInjury),
        },
      });
      await api.claims.triage(claimId);
    },
    onSuccess: () => {
      sessionStorage.setItem(
        INCIDENT_DRAFT_KEY,
        JSON.stringify({
          claimId: activeClaimId || sessionStorage.getItem("activeClaimId") || null,
          step: 6,
          data,
        })
      );
      if (data.hasInjury) {
        navigate("/chat");
        return;
      }
      navigate("/assisted-mode");
    },
    onError: (err) => {
      toast({
        title: "Cannot continue",
        description: err instanceof Error ? err.message : "Please try again.",
        variant: "destructive",
      });
    },
  });

  const YesNo = ({ value, onChange }: { value: boolean | null; onChange: (v: boolean) => void }) => (
    <div className="flex gap-3">
      {[true, false].map((v) => (
        <Button key={String(v)} variant={value === v ? "default" : "outline"} className="flex-1 h-12" onClick={() => onChange(v)}>
          {v ? t("ii.yes") : t("ii.no")}
        </Button>
      ))}
    </div>
  );

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container pt-24 pb-16 px-4 max-w-3xl mx-auto">
        <div className="mb-8">
          <div className="overflow-x-auto no-scrollbar rounded-xl border border-border/60 bg-secondary/20 px-2 py-2">
            <div className="flex items-center gap-1 min-w-max">
              {STEPS.map((s, i) => {
                const Icon = s.icon;
                const done = i < step;
                const active = i === step;
                return (
                  <div key={s.id} className="flex items-center">
                    <button onClick={() => i < step && setStep(i)} className={`flex items-center gap-1.5 px-3 py-2 rounded-full text-xs font-medium transition-all ${active ? "bg-primary text-primary-foreground" : done ? "bg-primary/20 text-primary cursor-pointer" : "bg-secondary text-muted-foreground"}`}>
                      {done ? <Check className="w-3 h-3" /> : <Icon className="w-3 h-3" />}
                      <span className="hidden sm:inline">{s.label}</span>
                    </button>
                    {i < STEPS.length - 1 && <div className={`w-4 h-0.5 mx-1 ${i < step ? "bg-primary/40" : "bg-border"}`} />}
                  </div>
                );
              })}
            </div>
          </div>

          <div className="mt-2 h-1.5 rounded-full bg-secondary/70 border border-border/40 overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-primary/70 via-primary to-primary/70 transition-all duration-300"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>

        <Card className="border-border bg-card">
          <CardContent className="py-8 space-y-6">
            <div>
              <h2 className="text-xl font-display font-bold text-foreground">{currentStep.label}</h2>
              <p className="text-sm text-muted-foreground mt-1">{t("ii.step")} {step + 1} {t("ii.of")} {STEPS.length}</p>
            </div>

            {step === 0 && (
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {incidentTypes.map((it) => {
                  const Icon = it.icon;
                  return (
                    <button key={it.id} onClick={() => setData({ ...data, type: it.id })} className={`flex flex-col items-center gap-2 p-4 rounded-xl border-2 transition-all ${data.type === it.id ? "border-primary bg-primary/10" : "border-border hover:border-primary/40 bg-secondary/30"}`}>
                      <Icon className={`w-6 h-6 ${data.type === it.id ? "text-primary" : "text-muted-foreground"}`} />
                      <span className={`text-sm font-medium ${data.type === it.id ? "text-foreground" : "text-muted-foreground"}`}>{t(it.labelKey)}</span>
                    </button>
                  );
                })}
              </div>
            )}

            {step === 1 && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-2"><Label>{t("ii.date")}</Label><Input type="date" value={data.date} onChange={(e) => setData({ ...data, date: e.target.value })} /></div>
                <div className="space-y-2"><Label>{t("ii.time")}</Label><Input type="time" value={data.time} onChange={(e) => setData({ ...data, time: e.target.value })} /></div>
              </div>
            )}

            {step === 2 && (
              <div className="space-y-4">
                <div className="space-y-2"><Label>{t("ii.locationLabel")}</Label><Input placeholder={t("ii.locationPlaceholder")} value={data.location} onChange={(e) => setData({ ...data, location: e.target.value })} /></div>
                <Button variant="outline" size="sm" onClick={useCurrentLocation}><MapPin className="w-4 h-4 mr-1" /> {t("ii.useCurrentLocation")}</Button>
                {!googleMapsApiKey && (
                  <div className="w-full rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
                    Set `VITE_GOOGLE_MAPS_API_KEY` in frontend env to enable Google Maps.
                  </div>
                )}
                {mapError && googleMapsApiKey && (
                  <div className="w-full rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
                    {mapError}
                  </div>
                )}
                <div ref={mapContainerRef} className="w-full h-56 rounded-lg border border-border overflow-hidden" />
                <p className="text-xs text-muted-foreground">Click on map or drag marker to choose location.</p>
              </div>
            )}

            {step === 3 && (
              <div className="space-y-2">
                <Label>{t("ii.describeLabel")}</Label>
                <Textarea placeholder={t("ii.describePlaceholder")} rows={5} value={data.description} onChange={(e) => setData({ ...data, description: e.target.value })} />
                <p className="text-xs text-muted-foreground">{t("ii.describeHint")}</p>
              </div>
            )}

            {step === 4 && (
              <div className="space-y-4">
                <Label>{t("ii.thirdPartyQ")}</Label>
                <YesNo value={data.hasThirdParty} onChange={(v) => setData({ ...data, hasThirdParty: v })} />
                {data.hasThirdParty && (
                  <div className="space-y-2 animate-in fade-in duration-200">
                    <Label>{t("ii.thirdPartyDetails")}</Label>
                    <Textarea placeholder={t("ii.thirdPartyPlaceholder")} rows={3} value={data.thirdPartyInfo} onChange={(e) => setData({ ...data, thirdPartyInfo: e.target.value })} />
                  </div>
                )}
              </div>
            )}

            {step === 5 && (
              <div className="space-y-6">
                <div className="space-y-3"><Label>{t("ii.canDriveQ")}</Label><YesNo value={data.canDrive} onChange={(v) => setData({ ...data, canDrive: v })} /></div>
                {data.canDrive === false && (
                  <div className="space-y-3 animate-in fade-in duration-200"><Label>{t("ii.towingQ")}</Label><YesNo value={data.needsTowing} onChange={(v) => setData({ ...data, needsTowing: v })} /></div>
                )}
              </div>
            )}

            {step === 6 && (
              <div className="space-y-4">
                <Label>{t("ii.injuryQ")}</Label>
                <YesNo value={data.hasInjury} onChange={(v) => setData({ ...data, hasInjury: v })} />
                {data.hasInjury && (
                  <div className="p-4 rounded-lg bg-destructive/10 border border-destructive/30 animate-in fade-in duration-200">
                    <p className="text-sm font-medium text-destructive">{t("ii.injuryWarning")}</p>
                  </div>
                )}
              </div>
            )}

            <div className="flex justify-between pt-4">
              <Button variant="outline" onClick={() => step > 0 ? setStep(step - 1) : navigate("/start-claim")}>
                <ChevronLeft className="w-4 h-4 mr-1" /> {step > 0 ? t("ii.back") : t("ii.cancel")}
              </Button>
              <Button onClick={handleNext} disabled={!canNext()}>
                {step < STEPS.length - 1 ? t("ii.next") : t("ii.continue")} <ChevronRight className="w-4 h-4 ml-1" />
              </Button>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
