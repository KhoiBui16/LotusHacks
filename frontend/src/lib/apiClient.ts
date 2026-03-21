type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

export class ApiError extends Error {
  status: number;
  details: unknown;

  constructor(message: string, status: number, details: unknown) {
    super(message);
    this.status = status;
    this.details = details;
  }
}

function getBaseUrl(): string {
  const fromEnv = import.meta.env.VITE_API_BASE_URL as string | undefined;
  return (fromEnv && fromEnv.trim()) || "http://localhost:8000";
}

export function getAccessToken(): string | null {
  const raw = localStorage.getItem("vetc_auth");
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as { accessToken?: string };
    return parsed.accessToken ?? null;
  } catch {
    return null;
  }
}

export async function apiRequest<T>(
  path: string,
  options?: {
    method?: HttpMethod;
    body?: unknown;
    headers?: Record<string, string>;
    auth?: boolean;
  }
): Promise<T> {
  const method = options?.method ?? "GET";
  const headers: Record<string, string> = { ...(options?.headers ?? {}) };

  const auth = options?.auth ?? false;
  if (auth) {
    const token = getAccessToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  const isFormData = typeof FormData !== "undefined" && options?.body instanceof FormData;
  if (!isFormData) {
    headers["Content-Type"] = headers["Content-Type"] ?? "application/json";
  }

  const res = await fetch(`${getBaseUrl()}${path}`, {
    method,
    headers,
    body: options?.body
      ? isFormData
        ? (options.body as BodyInit)
        : JSON.stringify(options.body)
      : undefined,
  });

  const contentType = res.headers.get("content-type") ?? "";
  const payload = contentType.includes("application/json") ? await res.json() : await res.text();

  if (!res.ok) {
    let message = res.statusText || "Request failed";
    if (payload && typeof payload === "object" && "detail" in payload) {
      const detail = (payload as Record<string, unknown>).detail;
      if (typeof detail === "string" && detail.trim()) message = detail;
    }
    throw new ApiError(String(message), res.status, payload);
  }

  return payload as T;
}
