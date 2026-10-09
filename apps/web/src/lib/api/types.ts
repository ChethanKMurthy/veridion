/** Types mirroring the Veridion API (apps/api/src/veridion/api/serializers.py). */

export type Status = "supported" | "partially_supported" | "not_found" | "conflicting" | "human_review";
export type Role = "owner" | "admin" | "analyst" | "reviewer" | "viewer";
export type Mode = "rules" | "hybrid";

export interface Me {
  user: { id: string; name: string; email: string; created_at: string };
  organization: { id: string; name: string; slug: string; plan: string; is_demo: boolean };
  role: Role;
  memberships: { organization_id: string; organization: string; role: Role }[];
  is_platform_admin: boolean;
}

export interface Job {
  id: string;
  kind: string;
  status: "queued" | "running" | "succeeded" | "failed";
  progress: { stage?: string; pct?: number; message?: string };
  attempts: number;
  error: string | null;
  created_at: string;
  finished_at: string | null;
}

export interface Company {
  id: string;
  name: string;
  industry: string | null;
  country: string | null;
  size_band: string | null;
  fiscal_year_end: string;
  website: string | null;
  description: string | null;
  is_sample: boolean;
  created_at: string;
  document_count?: number;
  documents_ready?: number;
  pages?: number;
  periods?: string[];
  latest_run?: {
    id: string;
    summary: RunSummary;
    finished_at: string | null;
    requirement_set_id: string;
    mode: Mode;
    period_label: string | null;
  } | null;
  peer_ids?: string[];
  peers?: Company[];
}

export interface DocumentInfo {
  id: string;
  company_id: string;
  lineage_id: string;
  version: number;
  title: string;
  short_name: string;
  doc_type: string;
  filename: string;
  sha256: string;
  size_bytes: number;
  page_count: number | null;
  page_sizes: [number, number][];
  period_label: string | null;
  period_start: string | null;
  period_end: string | null;
  published_on: string | null;
  source_url: string | null;
  status: "uploaded" | "processing" | "ready" | "failed";
  error: string | null;
  ocr_pages: number[];
  stats: {
    passages?: number;
    tables?: number;
    metrics?: number;
    parse_ms?: number;
    total_ms?: number;
    warnings?: string[];
    ocr_pages?: number;
  };
  pipeline_version: string | null;
  extraction_version: string | null;
  is_sample: boolean;
  created_at: string;
  processed_at: string | null;
  superseded_at: string | null;
  superseded_by: string | null;
  job: Job | null;
  versions?: { id: string; version: number; sha256: string; created_at: string; superseded_at: string | null; status: string }[];
  cited_by_findings?: number;
}

export interface PassageDocRef {
  id: string;
  title: string;
  short_name: string;
  version?: number;
  doc_type?: string;
  period_label?: string | null;
  page_sizes?: [number, number][];
  superseded_at?: string | null;
}

export interface Passage {
  id: string;
  document_id: string;
  page: number;
  ordinal: number;
  kind: "paragraph" | "heading" | "list_item" | "table" | "table_row";
  section: string | null;
  text: string;
  bbox: [number, number, number, number];
  extraction_method: "text" | "ocr" | "table";
  confidence: number;
  table_ref: string | null;
  cells: { label?: string; values?: string[]; headers?: string[]; caption?: string; rows?: string[][] } | null;
  document: PassageDocRef | null;
  metrics?: { id: string; metric_key: string; value: number; unit: string | null; period_label: string | null }[];
  match?: SearchMatch;
}

export interface SearchMatch {
  score: number;
  bm25: number;
  terms: string[];
  phrases: string[];
  metrics: string[];
  section_match: boolean;
}

export interface PassageDetail extends Passage {
  page_passages: { id: string; kind: string; bbox: [number, number, number, number]; text: string }[];
  metrics: {
    id: string;
    metric_key: string;
    label: string | null;
    value: number;
    unit: string | null;
    normalized_value: number | null;
    normalized_unit: string | null;
    period_label: string | null;
    qualifiers: Record<string, unknown>;
    confidence: number;
  }[] & Passage["metrics"];
  cited_by: { finding_id: string; requirement_code: string; status: Status; run_id: string; role: string }[];
}

export interface ElementSpec {
  key: string;
  label: string;
  weight: number;
  check: { type: string; [k: string]: unknown };
  action: { title: string; detail: string; effort: "low" | "medium" | "high"; depends_on: string[] };
}

export interface Requirement {
  id: string;
  set_id: string;
  code: string;
  display_code: string;
  title: string;
  topic: string;
  summary: string;
  applicability: string | null;
  importance: number;
  elements: ElementSpec[];
  metric_keys: string[];
  search_terms: string[];
  source_reference: string;
  source_url: string | null;
  content_hash: string;
}

export interface RequirementSet {
  id: string;
  key: string;
  version: string;
  title: string;
  framework: string;
  description: string | null;
  standards: { name: string; url: string | null }[];
  effective_from: string | null;
  effective_to: string | null;
  effective_rule: string | null;
  status: "in_force" | "upcoming" | "withdrawn";
  review_status: "reviewed" | "draft";
  changelog: { version: string; date: string; changes: string[] }[];
  supersedes: string | null;
  succeeded_by: string | null;
  notes: string | null;
  content_hash: string;
  requirement_count: number;
  requirements?: Requirement[];
}

export interface RunSummary {
  counts?: Partial<Record<Status, number>>;
  requirements?: number;
  excluded?: number;
  average_completeness?: number;
  needs_review?: number;
  actions?: { created: number; updated: number; reopened: number; gap_closed: number };
}

export interface Run {
  id: string;
  company_id: string;
  requirement_set_id: string;
  requirement_set_title: string | null;
  mode: Mode;
  status: "queued" | "running" | "completed" | "failed";
  label: string | null;
  period_label: string | null;
  period_start: string | null;
  period_end: string | null;
  deadline: string | null;
  pipeline_version: string | null;
  extraction_version: string | null;
  rules_version: string | null;
  prompt_version: string | null;
  llm_provider: string | null;
  llm_model: string | null;
  llm_config: Record<string, unknown>;
  input_manifest: {
    documents?: { id: string; title: string; version: number; lineage_id: string; sha256: string; pipeline_version: string | null; period: string | null }[];
    requirement_set?: { id: string; content_hash: string };
    requirements?: Record<string, string>;
    period?: { label: string; start: string; end: string };
  };
  excluded_requirements: { code: string; display_code: string; rationale: string; decided_at: string }[];
  metrics: {
    timings?: Record<string, number>;
    llm?: { calls: number; cached: number; prompt_tokens: number; completion_tokens: number; failures: number };
    documents?: number;
    passages?: number;
    extracted_metrics?: number;
  };
  summary: RunSummary;
  previous_run_id: string | null;
  error: string | null;
  created_by: string | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  job: Job | null;
  stale_findings?: { finding_id: string; requirement_code: string; documents: { id: string; title: string; version: number }[] }[];
  created_by_name?: string | null;
}

export interface Priority {
  I?: number;
  G?: number;
  U?: number;
  P?: number;
  explanation?: string;
}

export interface ConflictValue {
  metric_id: string;
  passage_id: string;
  value: number;
  unit: string | null;
  normalized_value: number | null;
  normalized_unit: string | null;
  source: string;
  method: string;
  confidence: number;
}

export interface Conflict {
  metric_key: string;
  label: string;
  unit: string;
  period: string;
  relative_difference: number;
  low: ConflictValue;
  high: ConflictValue;
  values: ConflictValue[];
}

export interface Review {
  id: string;
  finding_id: string;
  reviewer_id: string | null;
  reviewer_name: string | null;
  decision: "accept" | "override" | "comment";
  previous_status: Status;
  new_status: Status | null;
  note: string;
  created_at: string;
}

export interface ReviewState {
  state: "unreviewed" | "accepted" | "overridden";
  effective_status: Status;
  latest: Review | null;
  count: number;
}

export interface FindingSummary {
  id: string;
  run_id: string;
  requirement_id: string;
  requirement_code: string;
  display_code: string;
  title: string;
  topic: string;
  importance: number;
  status: Status;
  completeness: number;
  confidence: number;
  requires_human_review: boolean;
  review_reasons: string[];
  missing_elements: string[];
  method: Mode;
  rules_status: Status | null;
  llm_status: Status | null;
  priority: Priority;
  rationale: string;
  evidence_count: number;
  primary_evidence: {
    passage_id: string;
    document_id: string;
    page: number;
    document: string | null;
    period_label: string | null;
    text: string;
    bbox: [number, number, number, number];
    role: string;
  } | null;
  conflicts: Conflict[];
  review: ReviewState;
  created_at: string;
  ordinal?: number;
}

export interface ElementResult {
  key: string;
  label: string;
  weight: number;
  status: "satisfied" | "missing" | "not_applicable";
  weak: boolean;
  passage_ids: string[];
  metric_ids: string[];
  note: string;
  source: "rules" | "model";
  context_passage_ids: string[];
}

export interface EvidenceLink {
  role: "supporting" | "conflicting" | "related";
  element_keys: string[];
  note: string | null;
  score: number;
  passage: Passage;
}

export interface Action {
  id: string;
  company_id: string;
  finding_id: string | null;
  run_id: string | null;
  set_key: string | null;
  requirement_code: string;
  gap_key: string;
  title: string;
  detail: string;
  rationale: string;
  owner: string | null;
  due_date: string | null;
  effort: "low" | "medium" | "high";
  priority_score: number;
  priority_components: Priority;
  status: "open" | "in_progress" | "blocked" | "done" | "dismissed";
  depends_on: string[];
  gap_closed_run_id: string | null;
  created_at: string;
  updated_at: string;
  company?: string | null;
}

export interface FindingTrail {
  finding: FindingSummary & {
    element_results: ElementResult[];
    rules_rationale: string;
    llm_output: {
      status: Status;
      rationale: string;
      confidence: number;
      requires_human_review: boolean;
      judgements: Record<string, { verdict: "yes" | "no" | "unclear"; note: string; evidence_ids: string[] }>;
      missing_elements: string[];
      overrides: { element: string | null; from: string; to: string; reason: string }[];
      cached: boolean;
      usage: Record<string, number>;
    } | null;
    citation_check: { cited?: string[]; invalid?: string[]; valid_ratio?: number; candidates?: number };
    retrieval: { hits?: ({ passage_id: string } & SearchMatch)[] };
  };
  requirement: Requirement;
  run: Run | null;
  evidence: EvidenceLink[];
  passages: Record<string, Passage>;
  reviews: Review[];
  actions: Action[];
  history: { finding_id: string; run_id: string; status: Status; completeness: number; requirement_set_id: string; mode: Mode; created_at: string }[];
}

export interface DiffItem {
  requirement_code: string;
  before: { status: Status; completeness: number; finding_id: string } | null;
  after: { status: Status; completeness: number; finding_id: string } | null;
  status_changed: boolean;
  evidence_added: string[];
  evidence_removed: string[];
  element_changes: { key: string; before: string | null; after: string | null }[];
  causes: string[];
}

export interface RunDiff {
  before_run_id: string;
  after_run_id: string;
  requirement_set_changed: boolean;
  requirement_sets: { before: string; after: string };
  document_changes: { change: string; title: string; document_id: string; from_version?: number; to_version?: number }[];
  version_changes: { field: string; before: string | null; after: string | null }[];
  items: DiffItem[];
  summary: string;
}

export interface MetricRow {
  id: string;
  metric_key: string;
  label: string;
  value: number;
  unit: string | null;
  normalized_value: number | null;
  normalized_unit: string | null;
  period_label: string | null;
  period_end: string | null;
  qualifiers: Record<string, unknown>;
  confidence: number;
  method: string;
  passage_id: string;
  document_id: string;
  document_title: string;
  page: number;
  source: string;
}

export interface KeyDisclosure {
  metric_key: string;
  label: string;
  current: MetricRow;
  prior: MetricRow | null;
  change: number | null;
  sources: number;
}

export interface Overview {
  company: Company;
  peers: Company[];
  coverage: {
    documents: number;
    ready: number;
    pages: number;
    periods: string[];
    doc_types: string[];
    ocr_pages: number;
    metrics: number;
  };
  documents: DocumentInfo[];
  key_disclosures: KeyDisclosure[];
  latest_run: Run | null;
  runs: Run[];
  unresolved: { finding_id: string; requirement_code: string; status: Status; reasons: string[] }[];
}

export interface BenchmarkNote {
  kind: "missing" | "method" | "conflict" | "converted" | "ocr" | "period" | "boundary" | "denominator" | "scope";
  text: string;
}

export interface BenchmarkCell {
  company_id: string;
  status: "disclosed" | "not_disclosed";
  value: number | null;
  unit?: string | null;
  normalized_value?: number | null;
  normalized_unit?: string | null;
  period_label?: string | null;
  period_start?: string | null;
  period_end?: string | null;
  passage_id?: string;
  document_id?: string;
  document_title?: string | null;
  source?: string | null;
  page?: number | null;
  method?: string;
  confidence?: number;
  qualifiers?: Record<string, unknown>;
  alternatives?: number;
  notes: BenchmarkNote[];
}

export interface Benchmark {
  period_label: string;
  companies: {
    id: string;
    name: string;
    is_focal: boolean;
    is_sample: boolean;
    fiscal_year_end: string;
    period: { label: string; start: string; end: string; description: string };
    boundary: { approach: string; passage_id: string; source: string } | null;
    documents: number;
  }[];
  rows: {
    metric_key: string;
    label: string;
    unit: string;
    question: string;
    lower_is_better: boolean | null;
    cells: BenchmarkCell[];
    coverage: string;
    comparable: boolean;
    comparability: string;
  }[];
  series: Record<string, Record<string, { period_label: string; period_end: string; value: number | null; unit: string | null; passage_id: string }[]>>;
}

export interface Dashboard {
  counts: { companies: number; documents: number; runs: number; open_actions: number };
  recent_runs: (Run & { company: string | null })[];
  review_queue: DashboardFinding[];
  contradictions: (DashboardFinding & { conflicts: Conflict[] })[];
  material_gaps: Action[];
  changes: { company_id: string; company: string; run_id: string; previous_run_id: string; summary: string; items: DiffItem[] }[];
  recent_documents: (DocumentInfo & { company: string | null })[];
  peer_coverage: { company_id: string; company: string; period: string; peers: string[]; metrics: { label: string; coverage: string; comparability: string }[] }[];
}

export interface DashboardFinding {
  finding_id: string;
  run_id: string;
  company_id: string;
  company: string;
  display_code: string;
  title: string;
  status: Status;
  reasons: string[];
  priority: number;
}

export interface Report {
  generated_at: string;
  generator: string;
  company: Company;
  run: Run;
  requirement_set: RequirementSet;
  findings: FindingSummary[];
  trails: Record<string, FindingTrail>;
  actions: Action[];
  limitations: string[];
}

export interface OrgInfo {
  id: string;
  name: string;
  slug: string;
  plan: string;
  is_demo: boolean;
  created_at: string;
  plan_details: {
    key: string;
    name: string;
    max_companies: number | null;
    max_documents: number | null;
    max_pages_per_document: number | null;
    runs_per_month: number | null;
    hybrid_runs_per_month: number | null;
    max_seats: number | null;
    exports: string[];
  };
  usage: Record<string, number | string>;
  llm_available: boolean;
}

export interface Member {
  id: string;
  user_id: string;
  name: string;
  email: string;
  role: Role;
  created_at: string;
  last_login_at: string | null;
}

export interface AuditEvent {
  id: string;
  action: string;
  actor_id: string | null;
  actor_name: string | null;
  entity_type: string | null;
  entity_id: string | null;
  data: Record<string, unknown>;
  created_at: string;
}
