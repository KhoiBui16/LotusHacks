import { useState } from "react";
import { Link } from "react-router-dom";
import { useLanguage } from "@/contexts/LanguageContext";
import Navbar from "@/components/landing/Navbar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Car, ShieldCheck, AlertTriangle, Plus, ChevronLeft, ChevronRight,
  FileText, Trash2, User, MapPin, Phone, Mail, CreditCard, Calendar,
  Weight, Users, Hash, Palette, Camera, X, Save, CheckCircle2
} from "lucide-react";

interface VehicleData {
  id: string;
  plate: string;
  model: string;
  year: number;
  color: string;
  vehicleType: string;
  seats: number;
  weight: string;
  chassisNumber: string;
  engineNumber: string;
  noPlateYet: boolean;
  usage: "personal" | "commercial";
  // Policy / Insurance
  policyLinked: boolean;
  policyId: string | null;
  insurer: string | null;
  expiry: string | null;
  effectiveDate: string | null;
  insuranceYears: number;
  premium: string;
  additionalBenefits: string[];
  // Buyer info
  buyerType: "individual" | "business";
  buyerName: string;
  buyerDob: string;
  buyerAge: number;
  buyerGender: string;
  buyerPhone: string;
  buyerEmail: string;
  buyerIdNumber: string;
  buyerAddress: string;
  // Owner info
  ownerSameAsBuyer: boolean;
  ownerName: string;
  ownerPhone: string;
  ownerEmail: string;
  ownerAddress: string;
  claims: number;
}

const mockVehicles: VehicleData[] = [
  {
    id: "v1", plate: "51A-123.45", model: "Toyota Camry 2.5Q", year: 2023, color: "White",
    vehicleType: "Sedan", seats: 5, weight: "1.57", chassisNumber: "JTDKN3DU5A0123456", engineNumber: "2AR-FE-7891011",
    noPlateYet: false, usage: "personal",
    policyLinked: true, policyId: "POL-2024-00891", insurer: "Bảo Việt", expiry: "2025-06-30",
    effectiveDate: "2024-06-30", insuranceYears: 2, premium: "4,200,000₫",
    additionalBenefits: ["Accident insurance for driver & passengers"],
    buyerType: "individual", buyerName: "Nguyễn Văn An", buyerDob: "1990-05-15", buyerAge: 35,
    buyerGender: "Male", buyerPhone: "+84 912 345 678", buyerEmail: "an.nguyen@email.com",
    buyerIdNumber: "079190012345", buyerAddress: "123 Nguyễn Huệ, Q.1, TP.HCM",
    ownerSameAsBuyer: true, ownerName: "Nguyễn Văn An", ownerPhone: "+84 912 345 678",
    ownerEmail: "an.nguyen@email.com", ownerAddress: "123 Nguyễn Huệ, Q.1, TP.HCM",
    claims: 2,
  },
  {
    id: "v2", plate: "30H-567.89", model: "Honda CR-V 1.5L", year: 2022, color: "Black",
    vehicleType: "SUV", seats: 7, weight: "1.69", chassisNumber: "2HKRW2H53MH654321", engineNumber: "L15B-4567890",
    noPlateYet: false, usage: "personal",
    policyLinked: false, policyId: null, insurer: null, expiry: null,
    effectiveDate: null, insuranceYears: 0, premium: "0₫",
    additionalBenefits: [],
    buyerType: "individual", buyerName: "Trần Thị Bình", buyerDob: "1988-11-20", buyerAge: 37,
    buyerGender: "Female", buyerPhone: "+84 903 456 789", buyerEmail: "binh.tran@email.com",
    buyerIdNumber: "001188098765", buyerAddress: "45 Láng Hạ, Đống Đa, Hà Nội",
    ownerSameAsBuyer: false, ownerName: "Trần Minh Châu", ownerPhone: "+84 909 111 222",
    ownerEmail: "chau.tm@email.com", ownerAddress: "78 Kim Mã, Ba Đình, Hà Nội",
    claims: 1,
  },
  {
    id: "v3", plate: "43A-999.01", model: "Mazda CX-5 2.0 Premium", year: 2024, color: "Red",
    vehicleType: "SUV", seats: 5, weight: "1.59", chassisNumber: "JM3KFBDM5R0987654", engineNumber: "PE-VPS-1234567",
    noPlateYet: false, usage: "commercial",
    policyLinked: true, policyId: "POL-2024-01234", insurer: "PVI Insurance", expiry: "2025-12-15",
    effectiveDate: "2024-12-15", insuranceYears: 1, premium: "5,800,000₫",
    additionalBenefits: ["Accident insurance for driver & passengers", "Flood / water damage coverage"],
    buyerType: "business", buyerName: "Công ty TNHH Minh Phát Logistics", buyerDob: "", buyerAge: 0,
    buyerGender: "", buyerPhone: "+84 286 123 456", buyerEmail: "info@minhphat.vn",
    buyerIdNumber: "0312345678", buyerAddress: "200 Võ Văn Kiệt, Q.1, TP.HCM",
    ownerSameAsBuyer: true, ownerName: "Công ty TNHH Minh Phát Logistics", ownerPhone: "+84 286 123 456",
    ownerEmail: "info@minhphat.vn", ownerAddress: "200 Võ Văn Kiệt, Q.1, TP.HCM",
    claims: 0,
  },
];

function InfoRow({ label, value, icon: Icon }: { label: string; value: string | number; icon?: React.ElementType }) {
  return (
    <div className="flex items-start gap-3 py-2.5 border-b border-border/50 last:border-0">
      {Icon && <Icon className="w-4 h-4 text-primary mt-0.5 shrink-0" />}
      <div className="min-w-0">
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="text-sm font-medium text-foreground break-words">{value || "—"}</p>
      </div>
    </div>
  );
}

export default function Vehicles() {
  const [selected, setSelected] = useState<string | null>("v1");
  const { t } = useLanguage();
  const vehicle = mockVehicles.find((v) => v.id === selected);

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container pt-24 pb-16 px-4 max-w-6xl mx-auto space-y-6">
        <Button variant="ghost" size="sm" asChild>
          <Link to="/dashboard"><ChevronLeft className="w-4 h-4 mr-1" /> {t("ct.dashboard")}</Link>
        </Button>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-display font-bold text-foreground">{t("vh.title")}</h1>
            <p className="text-muted-foreground mt-1">{t("vh.subtitle")}</p>
          </div>
          <Button size="sm"><Plus className="w-4 h-4 mr-1" /> {t("vh.addVehicle")}</Button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Vehicle List - Left */}
          <div className="lg:col-span-4 space-y-3">
            {mockVehicles.map((v) => (
              <Card
                key={v.id}
                className={`cursor-pointer transition-all border-2 ${selected === v.id ? "border-primary bg-primary/5" : "border-border hover:border-primary/40"}`}
                onClick={() => setSelected(v.id)}
              >
                <CardContent className="py-4 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-11 h-11 rounded-xl bg-secondary flex items-center justify-center">
                      <Car className="w-5 h-5 text-primary" />
                    </div>
                    <div>
                      <p className="font-display font-bold text-foreground text-sm">{v.plate}</p>
                      <p className="text-xs text-muted-foreground">{v.model}</p>
                      <p className="text-xs text-muted-foreground">{v.color} · {v.year}</p>
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    {v.policyLinked ? (
                      <Badge variant="outline" className="border-primary/40 text-primary bg-primary/10 gap-1 text-[10px]">
                        <ShieldCheck className="w-3 h-3" /> {t("vh.linked")}
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="border-yellow-500/40 text-yellow-600 bg-yellow-500/10 gap-1 text-[10px]">
                        <AlertTriangle className="w-3 h-3" /> {t("vh.noPolicy")}
                      </Badge>
                    )}
                    <span className="text-[10px] text-muted-foreground">{v.claims} {t("vh.claim(s)")}</span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Detail Panel - Right */}
          <div className="lg:col-span-8">
            {vehicle ? (
              <Tabs defaultValue="vehicle" className="space-y-4">
                <TabsList className="grid grid-cols-4 w-full">
                  <TabsTrigger value="vehicle">{t("vd.tabVehicle")}</TabsTrigger>
                  <TabsTrigger value="insurance">{t("vd.tabInsurance")}</TabsTrigger>
                  <TabsTrigger value="buyer">{t("vd.tabBuyer")}</TabsTrigger>
                  <TabsTrigger value="owner">{t("vd.tabOwner")}</TabsTrigger>
                </TabsList>

                {/* Tab 1: Vehicle Info */}
                <TabsContent value="vehicle" className="space-y-4">
                  <Card className="border-border bg-card">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-base flex items-center gap-2">
                        <Car className="w-4 h-4 text-primary" /> {t("vd.vehicleInfo")}
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-center gap-3 p-3 rounded-lg bg-secondary/50 mb-4">
                        <Camera className="w-5 h-5 text-primary" />
                        <div>
                          <p className="text-sm font-medium text-primary">{t("vd.quickScan")}</p>
                          <p className="text-xs text-muted-foreground">{t("vd.quickScanDesc")}</p>
                        </div>
                      </div>

                      <div className="mb-4">
                        <p className="text-xs text-muted-foreground mb-1">{t("vd.usage")}</p>
                        <div className="flex gap-3">
                          <Badge variant={vehicle.usage === "personal" ? "default" : "outline"} className="text-xs">
                            {t("vd.personal")}
                          </Badge>
                          <Badge variant={vehicle.usage === "commercial" ? "default" : "outline"} className="text-xs">
                            {t("vd.commercial")}
                          </Badge>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-x-6">
                        <InfoRow label={t("vd.vehicleType")} value={vehicle.vehicleType} icon={Car} />
                        <InfoRow label={t("vd.seats")} value={vehicle.seats} icon={Users} />
                        <InfoRow label={t("vd.weight")} value={`${vehicle.weight} ${t("vd.tons")}`} icon={Weight} />
                      </div>

                      <div className="flex items-center gap-3 py-3 border-b border-border/50">
                        <Switch checked={vehicle.noPlateYet} disabled />
                        <span className="text-sm text-muted-foreground">{t("vd.noPlateYet")}</span>
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-x-6">
                        <InfoRow label={t("vd.plateNumber")} value={vehicle.plate} icon={Hash} />
                        <InfoRow label={t("vd.chassisNumber")} value={vehicle.chassisNumber} icon={Hash} />
                        <InfoRow label={t("vd.engineNumber")} value={vehicle.engineNumber} icon={Hash} />
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-x-6">
                        <InfoRow label={t("vh.model")} value={vehicle.model} icon={Car} />
                        <InfoRow label={t("vh.year")} value={vehicle.year} icon={Calendar} />
                        <InfoRow label={t("vh.color")} value={vehicle.color} icon={Palette} />
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* Tab 2: Insurance / Policy */}
                <TabsContent value="insurance" className="space-y-4">
                  <Card className={`border-2 ${vehicle.policyLinked ? "border-primary/30 bg-primary/5" : "border-yellow-500/30 bg-yellow-500/5"}`}>
                    <CardHeader className="pb-2">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-base flex items-center gap-2">
                          <ShieldCheck className="w-4 h-4 text-primary" /> {t("vd.insuranceInfo")}
                        </CardTitle>
                        {vehicle.policyLinked ? (
                          <Badge className="bg-primary/10 text-primary border-primary/30 text-xs">{t("vh.linked")}</Badge>
                        ) : (
                          <Badge variant="outline" className="border-yellow-500/40 text-yellow-600 text-xs">{t("vh.noPolicy")}</Badge>
                        )}
                      </div>
                    </CardHeader>
                    <CardContent>
                      {vehicle.policyLinked ? (
                        <>
                          <div className="grid grid-cols-1 sm:grid-cols-3 gap-x-6">
                            <InfoRow label={t("vh.insurer")} value={vehicle.insurer || ""} icon={ShieldCheck} />
                            <InfoRow label={t("vh.policyId")} value={vehicle.policyId || ""} icon={FileText} />
                            <InfoRow label={t("vd.insuranceYears")} value={`${vehicle.insuranceYears} ${t("vd.years")}`} icon={Calendar} />
                          </div>
                          <div className="grid grid-cols-1 sm:grid-cols-3 gap-x-6">
                            <InfoRow label={t("vd.effectiveDate")} value={vehicle.effectiveDate || ""} icon={Calendar} />
                            <InfoRow label={t("vh.expiry")} value={vehicle.expiry || ""} icon={Calendar} />
                            <InfoRow label={t("vd.premium")} value={vehicle.premium} icon={CreditCard} />
                          </div>
                          {vehicle.additionalBenefits.length > 0 && (
                            <div className="mt-4 p-3 rounded-lg bg-secondary/50">
                              <p className="text-xs text-muted-foreground mb-2">{t("vd.additionalBenefits")}</p>
                              {vehicle.additionalBenefits.map((b, i) => (
                                <div key={i} className="flex items-center gap-2 text-sm text-foreground">
                                  <CheckCircle2 className="w-3.5 h-3.5 text-primary" />
                                  <span>{b}</span>
                                </div>
                              ))}
                            </div>
                          )}
                        </>
                      ) : (
                        <div className="text-center py-8">
                          <ShieldCheck className="w-10 h-10 text-muted-foreground mx-auto mb-3" />
                          <p className="text-sm text-muted-foreground mb-3">{t("vh.noPolicyLinked")}</p>
                          <Button size="sm"><Plus className="w-3 h-3 mr-1" /> {t("vh.linkPolicy")}</Button>
                        </div>
                      )}
                    </CardContent>
                  </Card>

                  {/* Claim History */}
                  <Card className="border-border bg-card">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-base flex items-center gap-2">
                        <FileText className="w-4 h-4 text-primary" /> {t("vh.claimHistory")}
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      {vehicle.claims > 0 ? (
                        <Link to="/claims" className="flex items-center justify-between p-3 rounded-lg bg-secondary/40 hover:bg-secondary/70 transition-colors">
                          <span className="text-sm text-muted-foreground">{t("vh.viewClaims")} {vehicle.claims} {t("vh.claim(s)")}</span>
                          <ChevronRight className="w-4 h-4 text-muted-foreground" />
                        </Link>
                      ) : (
                        <p className="text-sm text-muted-foreground py-4 text-center">{t("vh.noClaims")}</p>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* Tab 3: Buyer Info */}
                <TabsContent value="buyer" className="space-y-4">
                  <Card className="border-border bg-card">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-base flex items-center gap-2">
                        <User className="w-4 h-4 text-primary" /> {t("vd.buyerInfo")}
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="mb-4">
                        <p className="text-xs text-muted-foreground mb-1">{t("vd.buyerIs")}</p>
                        <div className="flex gap-3">
                          <Badge variant={vehicle.buyerType === "individual" ? "default" : "outline"} className="text-xs">
                            {t("vd.individual")}
                          </Badge>
                          <Badge variant={vehicle.buyerType === "business" ? "default" : "outline"} className="text-xs">
                            {t("vd.business")}
                          </Badge>
                        </div>
                      </div>

                      <div className="flex items-center gap-3 p-3 rounded-lg bg-secondary/50 mb-4">
                        <Camera className="w-5 h-5 text-primary" />
                        <div>
                          <p className="text-sm font-medium text-primary">{t("vd.quickScan")}</p>
                          <p className="text-xs text-muted-foreground">{t("vd.scanIdDesc")}</p>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-x-6">
                        <InfoRow label={t("vd.buyerName")} value={vehicle.buyerName} icon={User} />
                        {vehicle.buyerType === "individual" && (
                          <>
                            <InfoRow label={t("vd.dob")} value={vehicle.buyerDob} icon={Calendar} />
                            <InfoRow label={t("vd.age")} value={vehicle.buyerAge} />
                          </>
                        )}
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-x-6">
                        {vehicle.buyerType === "individual" && (
                          <InfoRow label={t("vd.gender")} value={vehicle.buyerGender} icon={User} />
                        )}
                        <InfoRow label={t("vd.phone")} value={vehicle.buyerPhone} icon={Phone} />
                        <InfoRow label={t("vd.email")} value={vehicle.buyerEmail} icon={Mail} />
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6">
                        <InfoRow label={t("vd.idNumber")} value={vehicle.buyerIdNumber} icon={CreditCard} />
                        <InfoRow label={t("vd.address")} value={vehicle.buyerAddress} icon={MapPin} />
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* Tab 4: Owner Info */}
                <TabsContent value="owner" className="space-y-4">
                  <Card className="border-border bg-card">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-base flex items-center gap-2">
                        <User className="w-4 h-4 text-primary" /> {t("vd.ownerInfo")}
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="mb-4">
                        <p className="text-xs text-muted-foreground mb-1">{t("vd.ownerIs")}</p>
                        <div className="flex gap-3">
                          <Badge variant={vehicle.ownerSameAsBuyer ? "default" : "outline"} className="text-xs">
                            {t("vd.sameAsBuyer")}
                          </Badge>
                          <Badge variant={!vehicle.ownerSameAsBuyer ? "default" : "outline"} className="text-xs">
                            {t("vd.different")}
                          </Badge>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-x-6">
                        <InfoRow label={t("vd.ownerName")} value={vehicle.ownerName} icon={User} />
                        <InfoRow label={t("vd.phone")} value={vehicle.ownerPhone} icon={Phone} />
                        <InfoRow label={t("vd.email")} value={vehicle.ownerEmail} icon={Mail} />
                      </div>
                      <div className="grid grid-cols-1 gap-x-6">
                        <InfoRow label={t("vd.address")} value={vehicle.ownerAddress} icon={MapPin} />
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>
              </Tabs>
            ) : (
              <Card className="border-border bg-card">
                <CardContent className="py-16 text-center">
                  <Car className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
                  <p className="text-sm text-muted-foreground">{t("vh.selectVehicle")}</p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
