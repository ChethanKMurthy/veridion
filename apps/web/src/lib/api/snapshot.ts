/**
 * The public demo reads API responses recorded from a real Veridion workspace
 * (`veridion demo snapshot`). Reviews and action updates are kept in memory for
 * the browser session so the guided scenario is fully interactive; anything that
 * would need the engine (uploads, new assessment runs) explains how to get access.
 */

import type {
  Action,
  Company,
  DocumentInfo,
  FindingSummary,
  FindingTrail,
  Passage,
  Review,
  ReviewState,
  Status,
} from "./types";
import { ApiError, DemoReadOnlyError, type DataClient, type Method, type Params } from "./client";

const ROOT = "/demo";

function snapshotFile(path: string, params?: Params): string {
  const clean = path.replace(/^\/+/, "");
  const entries = Object.entries(params ?? {})
    .filter(([, v]) => v !== undefined && v !== null && v !== "")
    .sort(([a], [b]) => a.localeCompare(b));
  const suffix = entries.length
    ? "@" + entries.map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`).join("@")
    : "";
  return `${ROOT}/api/${clean}${suffix}.json`;
}

function reviewState(reviews: Review[], status: Status): ReviewState {
  let state: ReviewState["state"] = "unreviewed";
  let effective: Status = status;
  let latest: Review | null = null;
  for (const r of reviews) {
    if (r.decision === "accept") {
      state = "accepted";
      effective = status;
      latest = r;
    } else if (r.decision === "override") {
      state = "overridden";
      effective = r.new_status ?? status;
      latest = r;
    }
  }
  return { state, effective_status: effective, latest, count: reviews.length };
}

const TOKEN = /[a-z0-9]+/g;
const STOP = new Set("a an and are as at be by for from has have in is it of on or our that the this to was were with we".split(" "));

function tokens(text: string): string[] {
  return (text.toLowerCase().match(TOKEN) ?? []).filter((t) => !STOP.has(t)).map((t) =>
    t.length > 3 && t.endsWith("s") && !t.endsWith("ss") ? t.slice(0, -1) : t,
  );
}

export class SnapshotClient implements DataClient {
  readonly mode = "demo" as const;
  readonly base = "/demo";
  private files = new Map<string, Promise<unknown>>();
  private reviews = new Map<string, Review[]>();
  private actions = new Map<string, Partial<Action>>();
  private counter = 0;

  private load<T>(file: string): Promise<T> {
    let pending = this.files.get(file);
    if (!pending) {
      pending = fetch(file).then(async (r) => {
        if (!r.ok) throw new ApiError(404, "This view is not part of the recorded demo. Request access to explore your own data.");
        return r.json();
      });
      pending.catch(() => this.files.delete(file));
      this.files.set(file, pending);
    }
    return pending as Promise<T>;
  }

  async get<T>(path: string, params?: Params): Promise<T> {
    if (path === "/search") return (await this.search(String(params?.company_id ?? ""), String(params?.q ?? ""))) as T;
    const data = await this.load<unknown>(snapshotFile(path, params));
    return this.overlay(path, structuredClone(data)) as T;
  }

  private mergeAction<A extends Action>(action: A): A {
    const patch = this.actions.get(action.id);
    return patch ? { ...action, ...patch } : action;
  }

  private withReviews(finding: FindingSummary): FindingSummary {
    const extra = this.reviews.get(finding.id);
    if (!extra?.length) return finding;
    const existingCount = finding.review.count;
    // Recorded reviews are summarised in `review`; re-derive the state including session reviews.
    const prior = finding.review.latest ? [finding.review.latest] : [];
    const state = reviewState([...prior, ...extra], finding.status);
    return { ...finding, review: { ...state, count: existingCount + extra.length } };
  }

  private overlay(path: string, data: unknown): unknown {
    if (/^\/runs\/[^/]+\/findings$/.test(path)) {
      return (data as FindingSummary[]).map((f) => this.withReviews(f));
    }
    if (/^\/findings\/[^/]+$/.test(path)) {
      const trail = data as FindingTrail;
      const extra = this.reviews.get(trail.finding.id) ?? [];
      trail.reviews = [...trail.reviews, ...extra];
      trail.finding = { ...trail.finding, ...this.withReviews(trail.finding) };
      trail.finding.review = reviewState(trail.reviews, trail.finding.status);
      trail.actions = trail.actions.map((a) => this.mergeAction(a));
      return trail;
    }
    if (/^\/companies\/[^/]+\/actions$/.test(path)) {
      return (data as Action[]).map((a) => this.mergeAction(a));
    }
    if (path === "/dashboard") {
      const d = data as { material_gaps: Action[] };
      d.material_gaps = d.material_gaps.map((a) => this.mergeAction(a));
      return d;
    }
    return data;
  }

  async send<T>(method: Method, path: string, body?: unknown): Promise<T> {
    const review = path.match(/^\/findings\/([^/]+)\/reviews$/);
    if (method === "POST" && review) {
      const input = body as { decision: Review["decision"]; new_status?: Status | null; note?: string };
      if (input.decision === "override" && !input.note?.trim()) {
        throw new ApiError(422, "Explain the override so the decision can be audited.");
      }
      const trail = await this.load<FindingTrail>(snapshotFile(`/findings/${review[1]}`));
      const created: Review = {
        id: `rev_demo_${++this.counter}`,
        finding_id: review[1],
        reviewer_id: null,
        reviewer_name: "You (demo session)",
        decision: input.decision,
        previous_status: trail.finding.status,
        new_status: input.decision === "override" ? (input.new_status ?? null) : null,
        note: input.note?.trim() ?? "",
        created_at: new Date().toISOString(),
      };
      this.reviews.set(review[1], [...(this.reviews.get(review[1]) ?? []), created]);
      return created as T;
    }
    const action = path.match(/^\/actions\/([^/]+)$/);
    if (method === "PATCH" && action) {
      const patch = { ...(this.actions.get(action[1]) ?? {}), ...(body as Partial<Action>), updated_at: new Date().toISOString() };
      this.actions.set(action[1], patch);
      return { id: action[1], ...patch } as T;
    }
    throw new DemoReadOnlyError();
  }

  async upload<T>(): Promise<T> {
    throw new DemoReadOnlyError("Uploading documents needs a workspace. Request access to analyse your own reports.");
  }

  pageImageUrl(documentId: string, page: number): string {
    return `${ROOT}/pages/${documentId}/${page}.png`;
  }

  fileUrl(): string | null {
    return null;
  }

  exportUrl(runId: string, format: "json" | "csv" | "md"): string {
    return `${ROOT}/exports/${runId}.${format}`;
  }

  /** Keyword search over the recorded passages, with the same "why it matched" explanation shape. */
  private async search(companyId: string, query: string) {
    const docs = await this.get<DocumentInfo[]>(`/companies/${companyId}/documents`);
    const pages = await Promise.all(
      docs.map(async (d) => ({ doc: d, passages: await this.get<Passage[]>(`/documents/${d.id}/passages`) })),
    );
    const qTokens = Array.from(new Set(tokens(query)));
    const all = pages.flatMap(({ doc, passages }) => passages.map((p) => ({ doc, p, t: tokens(p.text) })));
    const df = new Map<string, number>();
    for (const { t } of all) for (const term of new Set(t)) df.set(term, (df.get(term) ?? 0) + 1);
    const phrase = query.trim().toLowerCase();
    const scored = all
      .map(({ doc, p, t }) => {
        const tf = new Map<string, number>();
        for (const term of t) tf.set(term, (tf.get(term) ?? 0) + 1);
        const matched = qTokens.filter((q) => tf.has(q));
        let score = 0;
        for (const q of matched) {
          const idf = Math.log(1 + all.length / (df.get(q) ?? 1));
          score += (idf * (tf.get(q) ?? 0)) / ((tf.get(q) ?? 0) + 1.2 * (0.25 + 0.75 * (t.length / 40)));
        }
        const phraseHit = phrase.includes(" ") && p.text.toLowerCase().includes(phrase);
        if (phraseHit) score += 1.5;
        if (p.kind === "heading") score *= 0.35;
        if (p.kind === "table") score *= 0.6;
        return { doc, p, matched, phraseHit, score };
      })
      .filter((r) => r.score > 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, 12);
    const top = scored[0]?.score || 1;
    return {
      query,
      results: scored.map(({ doc, p, matched, phraseHit, score }) => ({
        ...p,
        document: { id: doc.id, title: doc.title, short_name: doc.short_name },
        match: {
          score: score / top,
          bm25: score,
          terms: matched,
          phrases: phraseHit ? [phrase] : [],
          metrics: (p.metrics ?? []).map((m) => m.metric_key),
          section_match: false,
        },
      })),
    };
  }
}

export type DemoManifest = {
  generated_at: string;
  organization: string;
  focal_company_id: string | null;
  company_ids: string[];
  page_scale: number;
  llm_model: string | null;
  notice: string;
};

export type { Company };
