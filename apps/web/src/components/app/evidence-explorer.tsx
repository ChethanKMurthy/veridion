"use client";

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState, useSyncExternalStore, type KeyboardEvent } from "react";
import { buttonClass } from "@/components/ui/button";
import { EmptyState, ErrorState, Notice, SkeletonRows } from "@/components/ui/feedback";
import { Segmented, Select } from "@/components/ui/field";
import { Download, Plus, Printer, Search } from "@/components/ui/icons";
import { CompletenessBar } from "@/components/ui/meter";
import { Dialog } from "@/components/ui/overlay";
import { StatusGlyph, StatusLabel } from "@/components/ui/status";
import { useApi, useClient, useHref } from "@/lib/api/context";
import type { FindingSummary, Run, Status } from "@/lib/api/types";
import { STATUS, cx, date, relative } from "@/lib/format";
import { useCompanyId } from "./company-frame";
import { FindingInspector } from "./finding-inspector";
import { NewRunDialog, RunProgress } from "./run-controls";

type Filter = "all" | "gaps" | Status;

const FILTERS: { value: Filter; label: string }[] = [
  { value: "all", label: "All" },
  { value: "gaps", label: "Gaps" },
  { value: "conflicting", label: STATUS.conflicting.short },
  { value: "human_review", label: STATUS.human_review.short },
  { value: "partially_supported", label: STATUS.partially_supported.short },
  { value: "not_found", label: STATUS.not_found.short },
  { value: "supported", label: STATUS.supported.short },
];

const WIDE_QUERY = "(min-width: 1280px)";

function subscribeWide(onChange: () => void) {
  const mq = window.matchMedia(WIDE_QUERY);
  mq.addEventListener("change", onChange);
  return () => mq.removeEventListener("change", onChange);
}

/** Whether the evidence trail fits beside the table (otherwise it opens as a drawer). */
function useIsWide() {
  return useSyncExternalStore(subscribeWide, () => window.matchMedia(WIDE_QUERY).matches, () => true);
}

function ReviewState({ finding }: { finding: FindingSummary }) {
  if (finding.review.state === "accepted") return <span className="text-forest">Accepted</span>;
  if (finding.review.state === "overridden") return <span className="text-brass-deep">Overridden</span>;
  if (finding.requires_human_review) return <span className="text-ink">Needs review</span>;
  return <span className="text-ink-muted">Unreviewed</span>;
}

export function EvidenceExplorer() {
  const companyId = useCompanyId();
  const router = useRouter();
  const pathname = usePathname();
  const search = useSearchParams();
  const client = useClient();
  const href = useHref();
  const wide = useIsWide();
  const [newRun, setNewRun] = useState(false);
  const [query, setQuery] = useState("");
  const tableRef = useRef<HTMLTableSectionElement>(null);

  const { data: runs, error: runsError, mutate: refreshRuns } = useApi<Run[]>(`/companies/${companyId}/runs`, undefined, {
    refreshInterval: (latest) => (latest?.some((r) => r.status === "queued" || r.status === "running") ? 1500 : 0),
  });
  const completed = runs?.filter((r) => r.status === "completed") ?? [];
  const pending = runs?.find((r) => r.status === "queued" || r.status === "running");
  const runId = search.get("run") ?? completed[0]?.id ?? null;
  const run = runs?.find((r) => r.id === runId);
  const findingId = search.get("finding");
  const filter = (search.get("status") as Filter) ?? "all";

  const { data: findings, error: findingsError, isLoading } = useApi<FindingSummary[]>(runId ? `/runs/${runId}/findings` : null);

  const setParam = useCallback(
    (key: string, value: string | null) => {
      const sp = new URLSearchParams(search.toString());
      if (value === null) sp.delete(key);
      else sp.set(key, value);
      router.replace(`${pathname}?${sp.toString()}`, { scroll: false });
    },
    [pathname, router, search],
  );

  const counts = useMemo(() => {
    const c: Record<string, number> = { all: findings?.length ?? 0, gaps: 0 };
    for (const f of findings ?? []) {
      const s = f.review.effective_status;
      c[s] = (c[s] ?? 0) + 1;
      if (s !== "supported") c.gaps += 1;
    }
    return c;
  }, [findings]);

  const rows = useMemo(() => {
    const q = query.trim().toLowerCase();
    return (findings ?? []).filter((f) => {
      const s = f.review.effective_status;
      const statusOk = filter === "all" ? true : filter === "gaps" ? s !== "supported" : s === filter;
      const queryOk = !q || `${f.display_code} ${f.title} ${f.topic}`.toLowerCase().includes(q);
      return statusOk && queryOk;
    });
  }, [findings, filter, query]);

  const select = (id: string | null) => setParam("finding", id);

  // The list and the table are both rendered; container queries show one of them.
  const visibleEntry = (id: string) =>
    [document.getElementById(`item-${id}`), document.getElementById(`row-${id}`)].find((el) => el && el.offsetParent !== null);

  const focusFinding = (id: string) => visibleEntry(id)?.focus();

  // Opening the trail narrows the list (the table becomes stacked entries); keep the selection in view.
  useEffect(() => {
    if (!findingId) return;
    const frame = requestAnimationFrame(() => {
      const entry = visibleEntry(findingId);
      (entry?.closest("li, tr") ?? entry)?.scrollIntoView({ block: "nearest" });
    });
    return () => cancelAnimationFrame(frame);
  }, [findingId]);

  const onKeyDown = (e: KeyboardEvent<HTMLElement>) => {
    if (!rows.length) return;
    const index = rows.findIndex((r) => r.id === findingId);
    if (e.key === "ArrowDown" || e.key === "j") {
      e.preventDefault();
      const next = rows[Math.min(rows.length - 1, index + 1)];
      select(next.id);
      focusFinding(next.id);
    } else if (e.key === "ArrowUp" || e.key === "k") {
      e.preventDefault();
      const prev = rows[Math.max(0, index - 1)];
      select(prev.id);
      focusFinding(prev.id);
    } else if (e.key === "Escape") {
      select(null);
    }
  };

  if (runsError) return <div className="p-6 lg:p-8"><ErrorState error={runsError} retry={() => refreshRuns()} /></div>;

  const inspectorOpen = Boolean(findingId);

  return (
    <div className={cx("grid min-h-[calc(100dvh-10rem)]", inspectorOpen && wide ? "grid-cols-[minmax(0,1fr)_var(--inspector-width)]" : "grid-cols-1")}>
      {/* A size container: layout follows the room left beside the sidebar and the evidence trail, not the viewport. */}
      <div className="@container min-w-0 px-4 py-5 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-3 @4xl:flex-row @4xl:items-center @4xl:justify-between">
          <div className="flex min-w-0 flex-wrap items-center gap-2">
            {completed.length ? (
              <Select
                aria-label="Assessment run"
                value={runId ?? ""}
                onChange={(e) => {
                  const sp = new URLSearchParams(search.toString());
                  sp.set("run", e.target.value);
                  sp.delete("finding");
                  router.replace(`${pathname}?${sp.toString()}`, { scroll: false });
                }}
                className="w-auto min-w-[18rem] max-w-full text-ui-sm"
              >
                {completed.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.requirement_set_id.replace("@", " v")} · {r.mode === "hybrid" ? "rules + model" : "rules"} · {date(r.finished_at)}
                  </option>
                ))}
              </Select>
            ) : null}
            {run ? (
              <span className="text-ui-sm text-ink-muted">
                {run.period_label} · {run.summary.requirements ?? 0} requirements
                {run.excluded_requirements.length ? ` · ${run.excluded_requirements.length} not applicable` : ""}
              </span>
            ) : null}
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {run ? (
              <>
                <Link href={href(`/reports/${run.id}`)} className={buttonClass("secondary", "sm")}>
                  <Printer size={14} /> Report
                </Link>
                <a href={client.exportUrl(run.id, "csv")} className={buttonClass("ghost", "sm")} download>
                  <Download size={14} /> CSV
                </a>
              </>
            ) : null}
            <button type="button" onClick={() => setNewRun(true)} className={buttonClass("primary", "sm")}>
              <Plus size={14} /> New assessment
            </button>
          </div>
        </div>

        {pending ? <RunProgress run={pending} className="mt-4" onDone={() => refreshRuns()} /> : null}
        {run?.stale_findings?.length ? (
          <Notice tone="warning" title="Some evidence has been replaced" className="mt-4">
            {run.stale_findings.length} finding{run.stale_findings.length === 1 ? "" : "s"} cite documents that now have a newer
            version. Run a new assessment to reassess them; this run is preserved as it was.
          </Notice>
        ) : null}

        <div className="mt-5 flex flex-col gap-3 @4xl:flex-row @4xl:items-center @4xl:justify-between">
          <Segmented
            label="Filter by status"
            value={filter}
            onChange={(v) => setParam("status", v === "all" ? null : v)}
            options={FILTERS.map((f) => ({ ...f, count: counts[f.value] ?? 0 }))}
            className="max-w-full overflow-x-auto no-scrollbar"
          />
          <label className="relative block @4xl:w-64">
            <span className="sr-only">Filter requirements</span>
            <Search size={14} className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-slate" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Filter requirements"
              className="h-8 w-full rounded-sm border border-rule-strong bg-surface pl-8 pr-2.5 text-ui-sm placeholder:text-ink-muted/80 focus:border-brass-deep focus:outline-none"
            />
          </label>
        </div>

        <div className="mt-4 overflow-x-auto rounded-sm border border-rule bg-surface scrollbar-quiet">
          {!runs || (runId && isLoading) ? (
            <div className="px-4"><SkeletonRows rows={9} /></div>
          ) : findingsError ? (
            <div className="p-4"><ErrorState error={findingsError} /></div>
          ) : !completed.length ? (
            <EmptyState
              className="m-4 border-none"
              title={pending ? "The first assessment is running" : "No assessment yet"}
              action={
                pending ? null : (
                  <button type="button" onClick={() => setNewRun(true)} className={buttonClass("primary", "sm")}>
                    <Plus size={14} /> Run an assessment
                  </button>
                )
              }
            >
              An assessment checks each requirement in a versioned catalogue against this company&apos;s documents and links every
              finding to the passages that support it.
            </EmptyState>
          ) : (
            <>
              {/* Narrow containers (phones, or beside the evidence trail): one stacked entry per requirement. */}
              <ul
                className="divide-y divide-rule @3xl:hidden"
                aria-label={`Findings for ${run?.requirement_set_id ?? "this run"}`}
                onKeyDown={onKeyDown}
              >
                {rows.map((f) => {
                  const active = f.id === findingId;
                  const effective = f.review.effective_status;
                  return (
                    <li
                      key={f.id}
                      className={cx(
                        "relative px-4 py-3.5 text-ui-sm transition-colors duration-150",
                        active ? "bg-brass-tint" : "has-[button:active]:bg-canvas has-[button:focus-visible]:bg-brass-tint",
                      )}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <button
                          id={`item-${f.id}`}
                          type="button"
                          onClick={() => select(f.id)}
                          aria-haspopup={wide ? undefined : "dialog"}
                          aria-current={active ? "true" : undefined}
                          className="min-w-0 text-left after:absolute after:inset-0 focus-visible:outline-none focus-visible:after:outline-2 focus-visible:after:-outline-offset-2 focus-visible:after:outline-brass-deep"
                        >
                          <span className="block font-mono text-[0.7rem] text-ink-muted">{f.display_code}</span>
                          <span className="mt-0.5 block text-ui font-medium leading-snug text-ink">{f.title}</span>
                        </button>
                        <span className="shrink-0 pt-0.5 text-right">
                          <StatusLabel status={effective} short />
                          {f.review.state === "overridden" ? (
                            <span className="mt-0.5 flex items-center justify-end gap-1 text-meta text-ink-muted">
                              was <StatusGlyph status={f.status} size={9} /> {STATUS[f.status].short.toLowerCase()}
                            </span>
                          ) : null}
                        </span>
                      </div>
                      <CompletenessBar value={f.completeness} className="mt-2.5" />
                      {f.missing_elements.length ? (
                        <p className="mt-1 text-meta text-ink-muted">Missing: {f.missing_elements.join("; ")}</p>
                      ) : null}
                      <p className="mt-2 flex items-baseline justify-between gap-3 text-meta text-ink-muted">
                        <span className="min-w-0 truncate">
                          {f.primary_evidence
                            ? `${f.primary_evidence.document} · p. ${f.primary_evidence.page}`
                            : "No source passage found"}
                        </span>
                        <span className="shrink-0">
                          <ReviewState finding={f} />
                        </span>
                      </p>
                    </li>
                  );
                })}
                {!rows.length ? <li className="px-4 py-10 text-center text-ui-sm text-ink-muted">No requirements match this filter.</li> : null}
              </ul>
              <table className="hidden w-full min-w-[680px] border-collapse text-left @3xl:table @4xl:min-w-[880px]">
                <caption className="sr-only">
                  Findings for {run?.requirement_set_id}. Use the arrow keys to move between rows and Enter to open the evidence trail.
                </caption>
                <thead className="sticky top-0 z-[1] bg-surface">
                  <tr className="border-b border-rule text-meta font-medium text-ink-muted">
                    <th scope="col" className="px-4 py-2.5 font-medium">Requirement</th>
                    <th scope="col" className="px-3 py-2.5 font-medium">Status</th>
                    <th scope="col" className="px-3 py-2.5 font-medium">Evidence coverage</th>
                    <th scope="col" className="px-3 py-2.5 font-medium">Primary source</th>
                    {/* Secondary columns: the period is in the run header and every row shares one assessment time. */}
                    <th scope="col" className="hidden px-3 py-2.5 font-medium @4xl:table-cell">Period</th>
                    <th scope="col" className="hidden px-3 py-2.5 font-medium @4xl:table-cell">Assessed</th>
                    <th scope="col" className="px-4 py-2.5 font-medium">Review</th>
                  </tr>
                </thead>
                <tbody ref={tableRef} onKeyDown={onKeyDown}>
                  {rows.map((f) => {
                    const active = f.id === findingId;
                    const effective = f.review.effective_status;
                    return (
                      <tr
                        key={f.id}
                        id={`row-${f.id}`}
                        tabIndex={0}
                        aria-selected={active}
                        onClick={() => select(f.id)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter" || e.key === " ") {
                            e.preventDefault();
                            select(f.id);
                          }
                        }}
                        className={cx(
                          "cursor-pointer border-b border-rule align-top text-ui-sm transition-colors duration-150 last:border-b-0 focus:outline-none focus-visible:bg-brass-tint",
                          active ? "bg-brass-tint" : "hover:bg-canvas",
                        )}
                      >
                        <td className="max-w-[22rem] px-4 py-3">
                          <span className="block font-mono text-[0.7rem] text-ink-muted">{f.display_code}</span>
                          <span className="mt-0.5 block font-medium leading-snug text-ink">{f.title}</span>
                        </td>
                        <td className="px-3 py-3">
                          <StatusLabel status={effective} short />
                          {f.review.state === "overridden" ? (
                            <span className="mt-1 flex items-center gap-1 text-meta text-ink-muted">
                              was <StatusGlyph status={f.status} size={9} /> {STATUS[f.status].short.toLowerCase()}
                            </span>
                          ) : null}
                        </td>
                        <td className="px-3 py-3">
                          <CompletenessBar value={f.completeness} />
                          {f.missing_elements.length ? (
                            <span className="mt-1 block max-w-[10rem] truncate text-meta text-ink-muted @4xl:max-w-[14rem]" title={f.missing_elements.join("; ")}>
                              Missing: {f.missing_elements.join("; ")}
                            </span>
                          ) : null}
                        </td>
                        <td className="px-3 py-3">
                          {f.primary_evidence ? (
                            <>
                              <span className="block max-w-[9rem] truncate text-ink @4xl:max-w-[12rem]" title={f.primary_evidence.document ?? undefined}>
                                {f.primary_evidence.document}
                              </span>
                              <span className="tnum block text-meta text-ink-muted">
                                Page {f.primary_evidence.page} · {f.evidence_count} passage{f.evidence_count === 1 ? "" : "s"}
                              </span>
                            </>
                          ) : (
                            <span className="text-ink-muted">None found</span>
                          )}
                        </td>
                        <td className="hidden px-3 py-3 text-ink-muted @4xl:table-cell">
                          {f.primary_evidence?.period_label ?? run?.period_label ?? "—"}
                        </td>
                        <td className="hidden px-3 py-3 text-ink-muted @4xl:table-cell">
                          <span className="block">{relative(run?.finished_at)}</span>
                          <span className="block text-meta">{f.method === "hybrid" ? "Rules + model" : "Rules"}</span>
                        </td>
                        <td className="px-4 py-3">
                          <ReviewState finding={f} />
                        </td>
                      </tr>
                    );
                  })}
                  {!rows.length ? (
                    <tr>
                      <td colSpan={7} className="px-4 py-10 text-center text-ui-sm text-ink-muted">
                        No requirements match this filter.
                      </td>
                    </tr>
                  ) : null}
                </tbody>
              </table>
            </>
          )}
        </div>
        {completed.length ? (
          <p className="mt-3 text-meta text-ink-muted">
            Status reflects the evidence in the documents provided, not a determination of compliance.
            <span className="hidden md:inline"> Use ↑ ↓ to move between requirements and Esc to close the trail.</span>
          </p>
        ) : null}
      </div>

      {inspectorOpen && wide ? (
        <aside
          aria-label="Evidence trail"
          className="sticky top-0 h-dvh min-h-0 border-l border-rule animate-panel-in"
        >
          <FindingInspector key={findingId} findingId={findingId!} companyId={companyId} onClose={() => select(null)} />
        </aside>
      ) : null}
      {!wide ? (
        <Dialog open={inspectorOpen} onClose={() => select(null)} title="Evidence trail" variant="drawer">
          {findingId ? (
            <div className="-mx-5 -my-5 h-[calc(100dvh-4.5rem)]">
              <FindingInspector key={findingId} findingId={findingId} companyId={companyId} />
            </div>
          ) : null}
        </Dialog>
      ) : null}

      <NewRunDialog
        open={newRun}
        onClose={() => setNewRun(false)}
        companyId={companyId}
        onCreated={(created) => {
          setNewRun(false);
          refreshRuns();
          const sp = new URLSearchParams(search.toString());
          sp.delete("run");
          sp.delete("finding");
          router.replace(`${pathname}?${sp.toString()}`, { scroll: false });
          void created;
        }}
      />
    </div>
  );
}
