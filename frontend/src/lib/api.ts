import { apiRequest } from "@/lib/apiClient";

export type AuthUser = {
  id: string;
  email: string;
  full_name: string;
  phone?: string | null;
  avatar_url?: string | null;
  created_at: string;
};

export type AuthResponse = {
  access_token: string;
  token_type: "bearer";
  user: AuthUser;
};

export type VehicleSummary = {
  id: string;
  plate: string | null;
  model: string;
  year: number;
  color: string;
  vehicle_type: string;
  policy_linked: boolean;
  insurer?: string | null;
  policy_id?: string | null;
  expiry?: string | null;
  claims_count: number;
  created_at: string;
};

export type VehicleDetail = {
  id: string;
  no_plate_yet?: boolean;
  plate?: string | null;
  model?: string;
  year?: number;
  color?: string;
  vehicle_type?: string;
  seats?: number | null;
  weight_tons?: number | null;
  chassis_number?: string | null;
  engine_number?: string | null;
  usage?: "personal" | "commercial";
  policy_linked?: boolean;
  policy_id?: string | null;
  insurer?: string | null;
  effective_date?: string | null;
  expiry?: string | null;
  insurance_years?: number | null;
  premium_amount?: number | null;
  premium_currency?: string | null;
  additional_benefits?: string[];
  buyer_type?: "individual" | "business";
  buyer_name?: string | null;
  buyer_dob?: string | null;
  buyer_age?: number | null;
  buyer_gender?: string | null;
  buyer_phone?: string | null;
  buyer_email?: string | null;
  buyer_id_number?: string | null;
  buyer_address?: string | null;
  owner_same_as_buyer?: boolean;
  owner_name?: string | null;
  owner_phone?: string | null;
  owner_email?: string | null;
  owner_address?: string | null;
};

export type ClaimListItem = {
  id: string;
  type: string;
  date: string;
  vehicle_plate: string | null;
  vehicle_id: string;
  insurer: string | null;
  status: "draft" | "processing" | "needs-docs" | "approved" | "rejected" | "closed";
  amount_value: number | null;
  amount_currency: string | null;
  updated_at: string;
};

export type ClaimIncident = {
  type: string;
  date: string;
  time?: string | null;
  location_text: string;
  description?: string | null;
  has_third_party: boolean;
  third_party_info?: string | null;
  can_drive: boolean;
  needs_towing: boolean;
  has_injury: boolean;
};

export type Claim = {
  id: string;
  vehicle_id: string;
  insurer?: string | null;
  policy_id?: string | null;
  status: string;
  incident?: ClaimIncident | null;
};

export type ClaimTimelineItem = {
  at: string;
  label: string;
  status: "done" | "current" | "pending";
};

export type ClaimDocument = {
  id: string;
  claim_id: string;
  doc_type: string;
  required: boolean;
  status: "pending" | "uploaded" | "error" | "valid" | "invalid" | "missing";
  note?: string | null;
  upload_id?: string | null;
  url?: string | null;
};

export type ValidationResult = {
  doc_type: string;
  status: "valid" | "invalid" | "missing";
  note?: string | null;
};

export type ValidationResponse = {
  overall: "ok" | "issues";
  results: ValidationResult[];
};

export type UploadResponse = {
  upload_id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  purpose: "claim_doc" | "policy_doc" | "avatar" | "other";
  url: string;
};

export type NotificationItem = {
  id: string;
  type: "status" | "docs" | "decision" | "info";
  title: string;
  message: string;
  claim_id?: string | null;
  read: boolean;
  created_at: string;
};

export type Settings = {
  push_notif: boolean;
  email_notif: boolean;
  in_app_notif: boolean;
  claim_updates: boolean;
  doc_reminders: boolean;
  marketing_emails: boolean;
  preferred_contact: "email" | "phone" | "chat";
  language: string;
};

export const api = {
  auth: {
    signup: (payload: { email: string; full_name: string; password: string }) =>
      apiRequest<AuthResponse>("/auth/signup", { method: "POST", body: payload }),
    signin: (payload: { email: string; password: string }) =>
      apiRequest<AuthResponse>("/auth/signin", { method: "POST", body: payload }),
    google: (payload: { id_token: string }) =>
      apiRequest<AuthResponse>("/auth/google", { method: "POST", body: payload }),
  },
  me: {
    get: () => apiRequest<AuthUser>("/me", { auth: true }),
    patch: (payload: { full_name?: string; phone?: string; avatar_url?: string }) =>
      apiRequest<AuthUser>("/me", { method: "PATCH", body: payload, auth: true }),
    changePassword: (payload: { current_password: string; new_password: string }) =>
      apiRequest<{ ok: boolean }>("/me/change-password", { method: "POST", body: payload, auth: true }),
  },
  vehicles: {
    list: () =>
      apiRequest<VehicleSummary[]>("/vehicles", { auth: true }),
    get: (id: string) => apiRequest<VehicleDetail>(`/vehicles/${id}`, { auth: true }),
  },
  claims: {
    list: (params: { status?: string; vehicle_id?: string; q?: string }) => {
      const usp = new URLSearchParams();
      if (params.status) usp.set("status", params.status);
      if (params.vehicle_id) usp.set("vehicle_id", params.vehicle_id);
      if (params.q) usp.set("q", params.q);
      const qs = usp.toString();
      return apiRequest<ClaimListItem[]>(`/claims${qs ? `?${qs}` : ""}`, { auth: true });
    },
    get: (id: string) => apiRequest<Claim>(`/claims/${id}`, { auth: true }),
    timeline: (id: string) => apiRequest<ClaimTimelineItem[]>(`/claims/${id}/timeline`, { auth: true }),
    documents: (id: string) => apiRequest<ClaimDocument[]>(`/claims/${id}/documents`, { auth: true }),
    submit: (id: string) => apiRequest<Claim>(`/claims/${id}/submit`, { method: "POST", body: { consent: true }, auth: true }),
    create: (payload: { vehicle_id: string; policy_id?: string; insurer?: string }) =>
      apiRequest<Claim>(`/claims`, { method: "POST", body: payload, auth: true }),
    patch: (id: string, payload: unknown) => apiRequest<Claim>(`/claims/${id}`, { method: "PATCH", body: payload, auth: true }),
    attachDocument: (claimId: string, payload: { doc_type: string; upload_id: string }) =>
      apiRequest<ClaimDocument>(`/claims/${claimId}/documents`, { method: "POST", body: payload, auth: true }),
    validate: (claimId: string) =>
      apiRequest<ValidationResponse>(`/claims/${claimId}/validate`, { method: "POST", auth: true }),
  },
  uploads: {
    upload: (file: File, purpose: "claim_doc" | "policy_doc" | "avatar" | "other" = "other") => {
      const form = new FormData();
      form.append("file", file);
      return apiRequest<UploadResponse>(`/uploads?purpose=${encodeURIComponent(purpose)}`, {
        method: "POST",
        body: form,
        auth: true,
      });
    },
  },
  notifications: {
    list: (tab?: "all" | "unread") => {
      const qs = tab ? `?tab=${encodeURIComponent(tab)}` : "";
      return apiRequest<NotificationItem[]>(`/notifications${qs}`, { auth: true });
    },
    read: (id: string) => apiRequest<{ ok: boolean }>(`/notifications/${id}/read`, { method: "POST", auth: true }),
    readAll: () => apiRequest<{ ok: boolean }>(`/notifications/read-all`, { method: "POST", auth: true }),
  },
  settings: {
    get: () => apiRequest<Settings>(`/settings`, { auth: true }),
    patch: (payload: Partial<Settings>) => apiRequest<Settings>(`/settings`, { method: "PATCH", body: payload, auth: true }),
  },
};
