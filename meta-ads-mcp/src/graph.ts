import type { AppConfig } from "./config.js";

export class GraphError extends Error {
  constructor(
    message: string,
    public readonly code?: number,
    public readonly subcode?: number,
    public readonly userMsg?: string,
  ) {
    super(message);
    this.name = "GraphError";
  }
}

type GraphParams = Record<string, string | number | boolean | undefined>;

export class GraphClient {
  constructor(private readonly config: AppConfig) {}

  private baseUrl(): string {
    return `https://graph.facebook.com/${this.config.apiVersion}`;
  }

  async get<T = unknown>(
    path: string,
    params: GraphParams = {},
  ): Promise<T> {
    return this.request<T>("GET", path, params);
  }

  async post<T = unknown>(
    path: string,
    body: GraphParams = {},
  ): Promise<T> {
    return this.request<T>("POST", path, body);
  }

  async postMultipart<T = unknown>(
    path: string,
    form: FormData,
  ): Promise<T> {
    const url = new URL(`${this.baseUrl()}/${path.replace(/^\//, "")}`);
    url.searchParams.set("access_token", this.config.accessToken);
    const res = await fetch(url, { method: "POST", body: form });
    const json = (await res.json()) as Record<string, unknown>;
    if (!res.ok || json.error) {
      throw this.fromPayload(json, res.status);
    }
    return json as T;
  }

  private async request<T>(
    method: "GET" | "POST",
    path: string,
    params: GraphParams,
  ): Promise<T> {
    const cleanPath = path.replace(/^\//, "");
    const url = new URL(`${this.baseUrl()}/${cleanPath}`);
    url.searchParams.set("access_token", this.config.accessToken);

    const body: Record<string, string> = {};
    for (const [k, v] of Object.entries(params)) {
      if (v === undefined) continue;
      if (method === "GET") {
        url.searchParams.set(k, String(v));
      } else {
        body[k] = String(v);
      }
    }

    let res: Response;
    if (method === "GET") {
      res = await fetch(url);
    } else {
      res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams(body),
      });
    }

    const json = (await res.json()) as Record<string, unknown>;
    if (!res.ok || json.error) {
      throw this.fromPayload(json, res.status);
    }
    return json as T;
  }

  private fromPayload(json: Record<string, unknown>, status: number): GraphError {
    const err = json.error as Record<string, unknown> | undefined;
    if (err) {
      return new GraphError(
        String(err.message || "Graph API error"),
        Number(err.code),
        err.error_subcode ? Number(err.error_subcode) : undefined,
        err.error_user_msg ? String(err.error_user_msg) : undefined,
      );
    }
    return new GraphError(`HTTP ${status}`);
  }

  adAccountPath(suffix = ""): string {
    const base = this.config.adAccountId;
    return suffix ? `${base}/${suffix}` : base;
  }

  async getWithRetry<T>(path: string, params: GraphParams = {}, tries = 3): Promise<T> {
    let last: unknown;
    for (let i = 0; i < tries; i++) {
      try {
        return await this.get<T>(path, params);
      } catch (e) {
        last = e;
        const code = e instanceof GraphError ? e.code : 0;
        if (code === 4 || code === 17 || code === 32) {
          await sleep(500 * (i + 1));
          continue;
        }
        throw e;
      }
    }
    throw last;
  }
}

function sleep(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms));
}

export function formatGraphError(e: unknown): string {
  if (e instanceof GraphError) {
    const parts = [e.message];
    if (e.userMsg) parts.push(e.userMsg);
    if (e.code) parts.push(`code=${e.code}`);
    return parts.join(" | ");
  }
  if (e instanceof Error) return e.message;
  return String(e);
}
