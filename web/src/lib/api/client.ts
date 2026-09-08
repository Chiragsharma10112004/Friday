const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
function getApiBaseUrl(): string {
  const envUrl = process.env.NEXT_PUBLIC_API_URL;
  if (envUrl && envUrl.trim()) {
    return envUrl.trim().replace(/\/$/, "");
  }

  // If in browser on a production domain and NEXT_PUBLIC_API_URL is missing:
  if (
    typeof window !== "undefined" &&
    window.location.hostname !== "localhost" &&
    window.location.hostname !== "127.0.0.1" &&
    !window.location.hostname.endsWith(".local")
  ) {
    return "";
  }

  return "http://localhost:8000";
}

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(status: number, message: string, data?: any) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

export async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const baseUrl = getApiBaseUrl();
  if (
    !baseUrl &&
    typeof window !== "undefined" &&
    window.location.hostname !== "localhost" &&
    window.location.hostname !== "127.0.0.1"
  ) {
    throw new ApiError(
      500,
      "NEXT_PUBLIC_API_URL is not configured for production. Set NEXT_PUBLIC_API_URL in your Vercel project settings to connect to your Render backend."
    );
  }

  const effectiveBaseUrl = baseUrl || "http://localhost:8000";
  const url = `${effectiveBaseUrl}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;

  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 45000);

  try {
    const response = await fetch(url, {
      ...options,
      headers,
      signal: options.signal || controller.signal,
    });
    clearTimeout(timeoutId);

    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
      } catch {
        errorData = await response.text();
      }
      const message =
        typeof errorData === "object" && errorData?.detail
          ? typeof errorData.detail === "string"
            ? errorData.detail
            : JSON.stringify(errorData.detail)
          : `HTTP ${response.status}: ${response.statusText}`;
      throw new ApiError(response.status, message, errorData);
    }

    if (response.status === 204) {
      return {} as T;
    }

    return (await response.json()) as T;
  } catch (error: any) {
    clearTimeout(timeoutId);
    if (error instanceof ApiError) {
      throw error;
    }
    if (error?.name === "AbortError") {
      throw new ApiError(
        408,
        "Request timed out. The backend server may be waking up from sleep.",
        error
      );
    }
    throw new ApiError(
      0,
      error?.message || "Failed to communicate with FRIDAY backend",
      error
    );
  }
}
