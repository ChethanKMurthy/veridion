/**
 * Data clients. Product screens are written once and run against either:
 *   - HttpClient     the live API (via the same-origin /api rewrite), used under /app
 *   - SnapshotClient recorded API responses, used by the public demo under /demo
 */

export type Params = Record<string, string | number | boolean | undefined | null>;
export type Method = "POST" | "PATCH" | "PUT" | "DELETE";

export class ApiError extends Error {
  status: number;
  code?: string;
  constructor(status: number, message: string, code?: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

/** Raised by the demo for actions that need a real workspace (uploads, new runs). */
export class DemoReadOnlyError extends ApiError {
  constructor(message = "The demo workspace is read-only. Request access to run this on your own documents.") {
    super(403, message, "demo_read_only");
  }
}

export interface DataClient {
  readonly mode: "live" | "demo";
  /** Path prefix for in-product links: "/app" or "/demo". */
  readonly base: string;
  get<T>(path: string, params?: Params): Promise<T>;
  send<T>(method: Method, path: string, body?: unknown): Promise<T>;
  upload<T>(path: string, form: FormData): Promise<T>;
  pageImageUrl(documentId: string, page: number): string;
  fileUrl(documentId: string): string | null;
  exportUrl(runId: string, format: "json" | "csv" | "md"): string;
}

export function queryString(params?: Params): string {
  if (!params) return "";
  const entries = Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== "");
  if (!entries.length) return "";
  const sp = new URLSearchParams();
  for (const [k, v] of entries) sp.set(k, String(v));
  return `?${sp.toString()}`;
}

async function parseError(response: Response): Promise<ApiError> {
  let message = `Request failed (${response.status})`;
  let code: string | undefined;
  try {
    const body = await response.json();
    if (typeof body?.detail === "string") message = body.detail;
    else if (Array.isArray(body?.detail)) {
      message = body.detail
        .map((d: { loc?: (string | number)[]; msg?: string }) =>
          `${(d.loc ?? []).filter((x) => x !== "body").join(".")}: ${d.msg}`.replace(/^: /, ""),
        )
        .join("; ");
    }
    code = body?.code;
  } catch {
    /* non-JSON error body */
  }
  if (response.status === 429) message = "Too many requests. Please wait a moment and try again.";
  return new ApiError(response.status, message, code);
}

export class HttpClient implements DataClient {
  readonly mode = "live" as const;
  readonly base = "/app";
  private readonly prefix = "/api/v1";

  async get<T>(path: string, params?: Params): Promise<T> {
    const response = await fetch(`${this.prefix}${path}${queryString(params)}`, {
      credentials: "same-origin",
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
    if (!response.ok) throw await parseError(response);
    return response.json() as Promise<T>;
  }

  async send<T>(method: Method, path: string, body?: unknown): Promise<T> {
    const response = await fetch(`${this.prefix}${path}`, {
      method,
      credentials: "same-origin",
      headers: { "Content-Type": "application/json", Accept: "application/json", "X-Veridion-Client": "web" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    if (!response.ok) throw await parseError(response);
    return response.status === 204 ? (undefined as T) : (response.json() as Promise<T>);
  }

  async upload<T>(path: string, form: FormData): Promise<T> {
    const response = await fetch(`${this.prefix}${path}`, {
      method: "POST",
      credentials: "same-origin",
      headers: { Accept: "application/json", "X-Veridion-Client": "web" },
      body: form,
    });
    if (!response.ok) throw await parseError(response);
    return response.json() as Promise<T>;
  }

  pageImageUrl(documentId: string, page: number): string {
    return `${this.prefix}/documents/${documentId}/pages/${page}/image?scale=1.5`;
  }

  fileUrl(documentId: string): string {
    return `${this.prefix}/documents/${documentId}/file`;
  }

  exportUrl(runId: string, format: "json" | "csv" | "md"): string {
    return `${this.prefix}/runs/${runId}/export?format=${format}`;
  }
}
