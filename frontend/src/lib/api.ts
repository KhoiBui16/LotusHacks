import { apiRequest } from "@/lib/apiClient";

export type AuthUser = {
  id: string;
  email: string;
  full_name: string;
  role?: "admin" | "user";
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
  _id?: string;
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

export type AIPipelineAssessment = {
  decision: string;
  score: number;
  reasons?: string[];
  flags?: string[];
  source_doc_type?: string | null;
  source_image_doc_type?: string | null;
  source_driver_license_doc_type?: string | null;
};

export type ValidationResponse = {
  overall: "ok" | "issues";
  results: ValidationResult[];
  ai_pipeline?: AIPipelineAssessment | null;
};

export type TriageResponse = {
  claim_id: string;
  risk_level: "low" | "medium" | "high";
  assisted_mode: boolean;
  reasons: string[];
};

export type CoverageCheck = {
  policy_active: boolean;
  has_policy: boolean;
  likely_excluded: boolean;
  deductible_notice?: string | null;
};

export type EligibilityResponse = {
  claim_id: string;
  outcome: "assisted_required" | "likely_covered" | "low_value_or_excluded";
  coverage: CoverageCheck;
  next_action: "assisted" | "chat" | "review" | "exit";
  notes: string[];
  advice_text?: string | null;
  recommended_actions?: string[];
  save_draft_available?: boolean;
  end_flow_available?: boolean;
};

export type ClaimChatBootstrapResponse = {
  claim_id: string;
  session_id: string;
  title: string;
  reused: boolean;
};

export type ClaimAdviceActionResponse = {
  claim_id: string;
  status: "draft" | "processing" | "needs-docs" | "approved" | "rejected" | "closed";
  message: string;
};

export type PolicyImportResponse = {
  claim_id: string;
  policy_linked: boolean;
  policy_id?: string | null;
  insurer?: string | null;
  source: string;
};

export type FirstNoticeResponse = {
  claim_id: string;
  captured: boolean;
  message: string;
};

export type DossierResponse = {
  claim_id: string;
  summary: string;
  timeline: Array<{ doc_type: string; status: "valid" | "invalid" | "missing"; note?: string | null }>;
  attachments_count: number;
  completeness: "complete" | "partial";
};

export type SubmitRouterResponse = {
  claim_id: string;
  channel: "api" | "email" | "portal";
  external_ref: string;
  status: "received" | "queued";
};

export type ClaimAppealResponse = {
  claim_id: string;
  appealed: boolean;
  message: string;
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

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
  source_tool?: string | null;
};

export type ChatSession = {
  id: string;
  title: string;
  claim_id?: string | null;
  workflow_stage?: string | null;
  messages: ChatMessage[];
  created_at: string;
  updated_at: string;
};

export type ChatSessionListItem = {
  id: string;
  title: string;
  updated_at: string;
  claim_id?: string | null;
  workflow_stage?: string | null;
};

export type AdminClaimListItem = ClaimListItem & {
  user_id: string;
  user_email: string;
  user_name: string;
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
    delete: (id: string) => apiRequest<{ ok: boolean }>(`/vehicles/${id}`, { method: "DELETE", auth: true }),
    update: (id: string, payload: Partial<VehicleDetail>) =>
      apiRequest<VehicleDetail>(`/vehicles/${id}`, { method: "PATCH", body: payload, auth: true }),
    create: (payload: {
      no_plate_yet: boolean;
      plate?: string | null;
      model: string;
      year: number;
      color: string;
      vehicle_type: string;
    }) => apiRequest<VehicleDetail>("/vehicles", { method: "POST", body: payload, auth: true }),
    linkPolicy: (
      id: string,
      payload: { policy_id: string; insurer: string; effective_date?: string; expiry?: string }
    ) => apiRequest<VehicleDetail>(`/vehicles/${id}/policy/link`, { method: "POST", body: payload, auth: true }),
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
    requiredDocs: (id: string) => apiRequest<Array<{ doc_type: string; required: boolean; title: string; mime_allowed: string[]; max_size_mb: number }>>(`/claims/${id}/required-docs`, { auth: true }),
    delete: (id: string) => apiRequest<{ ok: boolean }>(`/claims/${id}`, { method: "DELETE", auth: true }),
    documents: (id: string) => apiRequest<ClaimDocument[]>(`/claims/${id}/documents`, { auth: true }),
    submit: (id: string) => apiRequest<Claim>(`/claims/${id}/submit`, { method: "POST", body: { consent: true }, auth: true }),
    create: (payload: { vehicle_id: string; policy_id?: string; insurer?: string }) =>
      apiRequest<Claim>(`/claims`, { method: "POST", body: payload, auth: true }),
    patch: (id: string, payload: unknown) => apiRequest<Claim>(`/claims/${id}`, { method: "PATCH", body: payload, auth: true }),
    attachDocument: (claimId: string, payload: { doc_type: string; upload_id: string }) =>
      apiRequest<ClaimDocument>(`/claims/${claimId}/documents`, { method: "POST", body: payload, auth: true }),
    resetDocuments: (claimId: string) =>
      apiRequest<{ ok: boolean }>(`/claims/${claimId}/documents/reset`, { method: "POST", auth: true }),
    validate: (claimId: string) =>
      apiRequest<ValidationResponse>(`/claims/${claimId}/validate`, { method: "POST", auth: true }),
    triage: (claimId: string) =>
      apiRequest<TriageResponse>(`/claims/${claimId}/triage`, { method: "POST", auth: true }),
    eligibility: (claimId: string) =>
      apiRequest<EligibilityResponse>(`/claims/${claimId}/eligibility`, { auth: true }),
    bootstrapChat: (claimId: string) =>
      apiRequest<ClaimChatBootstrapResponse>(`/claims/${claimId}/chat-bootstrap`, { method: "POST", auth: true }),
    adviceAction: (claimId: string, payload: { action: "save_draft" | "end_flow" }) =>
      apiRequest<ClaimAdviceActionResponse>(`/claims/${claimId}/advice-action`, { method: "POST", body: payload, auth: true }),
    policyImport: (
      claimId: string,
      payload: { policy_id: string; insurer: string; effective_date?: string; expiry?: string; source?: "ocr" | "manual" | "upload" }
    ) => apiRequest<PolicyImportResponse>(`/claims/${claimId}/policy-import`, { method: "POST", body: payload, auth: true }),
    firstNotice: (
      claimId: string,
      payload: { emergency_contacted: boolean; kept_scene: boolean; initial_evidence_collected: boolean; notes?: string }
    ) => apiRequest<FirstNoticeResponse>(`/claims/${claimId}/first-notice`, { method: "POST", body: payload, auth: true }),
    dossier: (claimId: string) => apiRequest<DossierResponse>(`/claims/${claimId}/dossier`, { auth: true }),
    submitRouter: (claimId: string, payload: { channel: "api" | "email" | "portal" }) =>
      apiRequest<SubmitRouterResponse>(`/claims/${claimId}/submit-router`, { method: "POST", body: payload, auth: true }),
    appeal: (claimId: string, payload: { reason: string }) =>
      apiRequest<ClaimAppealResponse>(`/claims/${claimId}/appeal`, { method: "POST", body: payload, auth: true }),
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
  chat: {
    createSession: (payload?: { title?: string; claim_id?: string; workflow_stage?: string; context_seed?: string; seeded_from_eligibility?: boolean }) =>
      apiRequest<ChatSessionListItem>(`/chat/sessions`, { method: "POST", body: payload ?? {}, auth: true }),
    listSessions: () => apiRequest<ChatSessionListItem[]>(`/chat/sessions`, { auth: true }),
    getSession: (id: string) => apiRequest<ChatSession>(`/chat/sessions/${id}`, { auth: true }),
    sendMessage: (sessionId: string, payload: { content: string }) =>
      apiRequest<ChatSession>(`/chat/sessions/${sessionId}/messages`, { method: "POST", body: payload, auth: true }),
    deleteSession: (id: string) => apiRequest<{ ok: boolean }>(`/chat/sessions/${id}`, { method: "DELETE", auth: true }),
  },
  admin: {
    listClaims: (params: { status?: string; q?: string }) => {
      const usp = new URLSearchParams();
      if (params.status) usp.set("status", params.status);
      if (params.q) usp.set("q", params.q);
      const qs = usp.toString();
      return apiRequest<AdminClaimListItem[]>(`/admin/claims${qs ? `?${qs}` : ""}`, { auth: true });
    },
    updateClaimStatus: (claimId: string, payload: { status: string; note?: string }) =>
      apiRequest<{ ok: boolean }>(`/admin/claims/${claimId}/status`, { method: "POST", body: payload, auth: true }),
    deleteClaim: (claimId: string) =>
      apiRequest<{ ok: boolean }>(`/admin/claims/${claimId}`, { method: "DELETE", auth: true }),
    getClaim: (claimId: string) => apiRequest<Claim>(`/admin/claims/${claimId}`, { auth: true }),
    getClaimTimeline: (claimId: string) => apiRequest<ClaimTimelineItem[]>(`/admin/claims/${claimId}/timeline`, { auth: true }),
    getClaimDocuments: (claimId: string) => apiRequest<ClaimDocument[]>(`/admin/claims/${claimId}/documents`, { auth: true }),
    changeUserPassword: (payload: { email: string; new_password: string }) =>
      apiRequest<{ ok: boolean }>(`/admin/users/change-password`, { method: "POST", body: payload, auth: true }),
  },
};
