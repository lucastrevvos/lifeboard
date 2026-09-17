import type { Board, LoginInput, RegisterInput, User } from "./types";

const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

type ApiOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
};

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const headers = new Headers(options.headers);

  if (options.body !== undefined) {
    headers.set("Content-Type", "application/json");
  }

  let response: Response;

  try {
    response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers,
      credentials: "include",
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
    });
  } catch {
    throw new ApiError("Não foi possível conectar ao servidor. Tente novamente.", 0);
  }

  if (!response.ok) {
    let message = "Não foi possível concluir a solicitação.";

    try {
      const data = (await response.json()) as { detail?: string | Array<{ msg?: string }> };
      if (typeof data.detail === "string") {
        message = data.detail;
      } else if (Array.isArray(data.detail)) {
        message = data.detail.map((item) => item.msg).filter(Boolean).join(" ") || message;
      }
    } catch {
      // Keep the safe fallback for non-JSON error responses.
    }

    throw new ApiError(message, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export const api = {
  register: (data: RegisterInput) => request<User>("/api/auth/register", { method: "POST", body: data }),
  login: (data: LoginInput) => request<User>("/api/auth/login", { method: "POST", body: data }),
  logout: () => request<void>("/api/auth/logout", { method: "POST" }),
  currentUser: () => request<User>("/api/auth/me"),
  listBoards: () => request<Board[]>("/api/boards"),
  createBoard: (name: string) => request<Board>("/api/boards", { method: "POST", body: { name } }),
};

export function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Ocorreu um erro inesperado.";
}
