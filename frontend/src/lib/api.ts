const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Custom error class for API errors with status code and message.
 */
export class ApiError extends Error {
  public readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

/**
 * Turn a FastAPI error body into a readable message.
 * `detail` is a string for HTTPException and a list of validation errors for 422.
 */
function messageFromBody(body: unknown, fallback: string): string {
  if (typeof body !== "object" || body === null) return fallback;
  const { detail, message } = body as { detail?: unknown; message?: unknown };
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => (typeof item?.msg === "string" ? item.msg : "Invalid value"))
      .join("; ");
  }
  if (typeof message === "string") return message;
  return fallback;
}

/**
 * Low-level fetch wrapper with JSON handling and error management.
 * Paths include the API prefix, e.g. "/api/v1/cards".
 */
export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string> | undefined),
    },
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      message = messageFromBody(await response.json(), message);
    } catch {
      // Response body is not JSON; keep the default message
    }
    throw new ApiError(response.status, message);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

/**
 * Typed API client with convenience methods for each HTTP verb.
 */
export const api = {
  get<T>(path: string): Promise<T> {
    return apiFetch<T>(path, { method: "GET" });
  },

  post<T>(path: string, body?: unknown): Promise<T> {
    return apiFetch<T>(path, {
      method: "POST",
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  },

  patch<T>(path: string, body: unknown): Promise<T> {
    return apiFetch<T>(path, { method: "PATCH", body: JSON.stringify(body) });
  },

  put<T>(path: string, body?: unknown): Promise<T> {
    return apiFetch<T>(path, {
      method: "PUT",
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  },

  delete<T>(path: string): Promise<T> {
    return apiFetch<T>(path, { method: "DELETE" });
  },
};
