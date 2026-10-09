/**
 * A digest of the recorded demo workspace (written by `veridion demo snapshot`), used to show
 * real engine output — on fictional companies — on the marketing pages.
 */
import data from "@/content/demo-highlights.json";
import type { Action, BenchmarkCell, Conflict, RunDiff, RunSummary, Status } from "./api/types";

export type Crop = {
  src: string;
  size: [number, number];
  bbox: [number, number, number, number];
  document: string;
  title: string;
  page: number;
  text: string;
  id: string;
};

export type Highlights = {
  key_disclosures: {
    metric_key: string;
    label: string;
    current: { value: number; unit: string | null; period_label: string | null; source: string };
    prior: { value: number; unit: string | null; period_label: string | null } | null;
    change: number | null;
    sources: number;
  }[];
  company: { id: string; name: string; industry: string; country: string; fiscal_year_end: string };
  run: { id: string; requirement_set_id: string; mode: string; llm_model: string | null; period_label: string; summary: RunSummary; finished_at: string };
  findings: {
    id: string;
    display_code: string;
    title: string;
    status: Status;
    completeness: number;
    missing_elements: string[];
    primary_evidence: { document: string; page: number } | null;
    evidence_count: number;
    method: string;
  }[];
  conflict: {
    finding_id: string;
    display_code: string;
    title: string;
    rationale: string;
    conflict: Conflict;
    low: Crop | null;
    high: Crop | null;
    action: Action | null;
  } | null;
  benchmark: {
    companies: { id: string; name: string; is_focal: boolean; period: { description: string }; boundary: { approach: string } | null }[];
    rows: { metric_key: string; label: string; unit: string; question: string; cells: BenchmarkCell[]; comparability: string; coverage: string }[];
  };
  diff: RunDiff | null;
};

export const highlights = data as unknown as Highlights;
