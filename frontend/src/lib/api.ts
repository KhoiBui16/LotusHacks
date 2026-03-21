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
      apiRequest<
        Array<{
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
        }>
      >("/vehicles", { auth: true }),
    get: (id: string) => apiRequest<any>(`/vehicles/${id}`, { auth: true }),
  },
  claims: {
    list: (params: { status?: string; vehicle_id?: string; q?: string }) => {
      const usp = new URLSearchParams();
      if (params.status) usp.set("status", params.status);
      if (params.vehicle_id) usp.set("vehicle_id", params.vehicle_id);
      if (params.q) usp.set("q", params.q);
      const qs = usp.toString();
      return apiRequest<any[]>(`/claims${qs ? `?${qs}` : ""}`, { auth: true });
    },
    get: (id: string) => apiRequest<any>(`/claims/${id}`, { auth: true }),
    timeline: (id: string) => apiRequest<any[]>(`/claims/${id}/timeline`, { auth: true }),
  },
  notifications: {
    list: (tab?: "all" | "unread") => {
      const qs = tab ? `?tab=${encodeURIComponent(tab)}` : "";
      return apiRequest<any[]>(`/notifications${qs}`, { auth: true });
    },
    read: (id: string) => apiRequest<{ ok: boolean }>(`/notifications/${id}/read`, { method: "POST", auth: true }),
    readAll: () => apiRequest<{ ok: boolean }>(`/notifications/read-all`, { method: "POST", auth: true }),
  },
  settings: {
    get: () => apiRequest<any>(`/settings`, { auth: true }),
    patch: (payload: any) => apiRequest<any>(`/settings`, { method: "PATCH", body: payload, auth: true }),
  },
};

