import type { Status } from "./api/types";

export function cx(...classes: (string | false | null | undefined)[]): string {
  return classes.filter(Boolean).join(" ");
}

export const STATUS: Record<Status, { label: string; short: string; description: string }> = {
  supported: {
    label: "Supported",
    short: "Supported",
    description: "Every applicable element of the requirement is evidenced in the documents assessed.",
  },
  partially_supported: {
    label: "Partially supported",
    short: "Partial",
    description: "Some elements are evidenced; others are missing or only related disclosure was found.",
  },
  not_found: {
    label: "Evidence not found",
    short: "Not found",
    description:
      "No required element was found in the documents provided. This is not a finding of non-compliance.",
  },
  conflicting: {
    label: "Conflicting evidence",
    short: "Conflicting",
    description: "Sources disagree on a material value. A reviewer must confirm which figure is correct.",
  },
  human_review: {
    label: "Human review required",
    short: "Review",
    description: "The evidence cannot be resolved automatically and needs a reviewer's judgement.",
  },
};

export const STATUS_ORDER: Status[] = ["conflicting", "human_review", "partially_supported", "not_found", "supported"];

export const DOC_TYPES: Record<string, string> = {
  annual_report: "Annual report",
  sustainability_report: "Sustainability report",
  policy: "Policy",
  data_sheet: "Data sheet",
  other: "Other",
};

const nf0 = new Intl.NumberFormat("en-GB", { maximumFractionDigits: 0 });
const nf1 = new Intl.NumberFormat("en-GB", { maximumFractionDigits: 1 });
const nf3 = new Intl.NumberFormat("en-GB", { maximumSignificantDigits: 3 });

export function num(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  const abs = Math.abs(value);
  if (abs >= 100) return nf0.format(value);
  if (abs >= 10) return nf1.format(value);
  return nf3.format(value);
}

export function compact(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return new Intl.NumberFormat("en-GB", { notation: "compact", maximumFractionDigits: 1 }).format(value);
}

export function pct(value: number | null | undefined, digits = 0): string {
  if (value === null || value === undefined) return "—";
  return `${(value * 100).toFixed(digits)}%`;
}

export function signedPct(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  const s = (value * 100).toFixed(1);
  return `${value > 0 ? "+" : value < 0 ? "−" : ""}${s.replace("-", "")}%`;
}

/** tCO2e → tCO₂e for display. */
export function unit(u: string | null | undefined): string {
  if (!u) return "";
  return u.replace(/CO2/g, "CO₂").replace(/\bm3\b/g, "m³");
}

const dateFmt = new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short", year: "numeric" });
const dateTimeFmt = new Intl.DateTimeFormat("en-GB", {
  day: "numeric",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

export function date(value: string | null | undefined): string {
  if (!value) return "—";
  const d = new Date(value.length === 10 ? `${value}T00:00:00` : value);
  return Number.isNaN(d.getTime()) ? value : dateFmt.format(d);
}

export function dateTime(value: string | null | undefined): string {
  if (!value) return "—";
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? value : dateTimeFmt.format(d);
}

export function relative(value: string | null | undefined, now = Date.now()): string {
  if (!value) return "—";
  const then = new Date(value).getTime();
  const s = Math.round((now - then) / 1000);
  if (s < 45) return "just now";
  const m = Math.round(s / 60);
  if (m < 60) return `${m} min ago`;
  const h = Math.round(m / 60);
  if (h < 24) return `${h} h ago`;
  const d = Math.round(h / 24);
  if (d < 14) return `${d} day${d === 1 ? "" : "s"} ago`;
  return date(value);
}

export function bytes(n: number | null | undefined): string {
  if (!n) return "—";
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(0)} KB`;
  return `${(n / 1024 / 1024).toFixed(1)} MB`;
}

export function fiscalYearLabel(fye: string): string {
  const [m, d] = fye.split("-").map(Number);
  if (m === 12 && d === 31) return "Calendar year";
  const month = new Date(2000, (m || 1) - 1, 1).toLocaleString("en-GB", { month: "long" });
  return `Year ending ${d} ${month}`;
}

export function shortId(id: string | null | undefined, n = 8): string {
  if (!id) return "—";
  const [prefix, rest] = id.includes("_") ? id.split("_", 2) : ["", id];
  return prefix ? `${prefix}_${rest.slice(-n)}` : id.slice(-n);
}

export function plural(n: number, word: string, pluralWord = `${word}s`): string {
  return `${n} ${n === 1 ? word : pluralWord}`;
}

export const EFFORT_LABEL: Record<string, string> = { low: "Low effort", medium: "Medium effort", high: "High effort" };

export const ACTION_STATUS: Record<string, string> = {
  open: "Open",
  in_progress: "In progress",
  blocked: "Blocked",
  done: "Done",
  dismissed: "Dismissed",
};
