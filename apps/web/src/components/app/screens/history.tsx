"use client";

import Link from "next/link";
import { useState } from "react";
import { EmptyState, ErrorState, Notice, ScreenSkeleton, Skeleton } from "@/components/ui/feedback";
import { Select } from "@/components/ui/field";
import { ArrowRight } from "@/components/ui/icons";
import { IdTag } from "@/components/ui/overlay";
import { StatusLabel } from "@/components/ui/status";
import { useApi, useHref } from "@/lib/api/context";
import type { Run, RunDiff } from "@/lib/api/types";
import { cx, dateTime, num, pct } from "@/lib/format";
import { PageHeader, Section } from "../shell";
import { useCompanyId } from "../company-frame";
import { StatusDistribution } from "./company-overview";

function runLabel(r: Run) {
  return `${r.requirement_set_id.replace("@", " v")} · ${r.mode === "hybrid" ? "rules + model" : "rules"} · ${dateTime(r.finished_at ?? r.created_at)}`;
}

function DiffView({ before, after, companyId, isPrevious }: { before: string; after: string; companyId: string; isPrevious: boolean }) {
  const href = useHref();
  // Comparing with the immediately preceding run needs no parameter (and is what the demo recorded).
  const { data, error } = useApi<RunDiff>(`/runs/${after}/diff`, isPrevious ? undefined : { against: before });
  if (error) return <ErrorState error={error} />;
  if (!data) return <Skeleton className="h-48" />;
  return (
    <div className="space-y-5">
      <p className="text-ui text-ink">{data.summary}.</p>
      {data.requirement_set_changed || data.document_changes.length || data.version_changes.length ? (
        <dl className="grid gap-x-6 gap-y-2 rounded-sm border border-rule bg-surface p-4 text-ui-sm sm:grid-cols-[10rem_1fr]">
          {data.requirement_set_changed ? (
            <>
              <dt className="text-ink-muted">Catalogue</dt>
              <dd className="font-mono text-[0.75rem] text-ink">
                {data.requirement_sets.before} → {data.requirement_sets.after}
              </dd>
            </>
          ) : null}
          {data.document_changes.map((d, i) => (
            <div key={i} className="contents">
              <dt className="text-ink-muted">Document {d.change}</dt>
              <dd className="text-ink">
                {d.title}
                {d.from_version ? ` (v${d.from_version} → v${d.to_version})` : ""}
              </dd>
            </div>
          ))}
          {data.version_changes.map((v) => (
            <div key={v.field} className="contents">
              <dt className="text-ink-muted">{v.field.replace("_", " ")}</dt>
              <dd className="font-mono text-[0.75rem] text-ink">
                {v.before ?? "—"} → {v.after ?? "—"}
              </dd>
            </div>
          ))}
        </dl>
      ) : null}
      {data.items.length ? (
        <div className="overflow-x-auto rounded-sm border border-rule bg-surface scrollbar-quiet">
          <table className="w-full min-w-[760px] text-left text-ui-sm">
            <thead>
              <tr className="border-b border-rule text-meta text-ink-muted">
                <th scope="col" className="px-4 py-2.5 font-medium">Requirement</th>
                <th scope="col" className="px-3 py-2.5 font-medium">Before</th>
                <th scope="col" className="px-3 py-2.5 font-medium"><span className="sr-only">changed to</span></th>
                <th scope="col" className="px-3 py-2.5 font-medium">After</th>
                <th scope="col" className="px-3 py-2.5 font-medium">What changed</th>
                <th scope="col" className="px-4 py-2.5 font-medium">Why</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((item) => (
                <tr key={item.requirement_code} className="border-b border-rule align-top last:border-0">
                  <td className="px-4 py-3 font-mono text-[0.75rem] text-ink">
                    {item.after ? (
                      <Link href={href(`/companies/${companyId}/evidence?run=${after}&finding=${item.after.finding_id}`)} className="hover:underline">
                        {item.requirement_code}
                      </Link>
                    ) : (
                      item.requirement_code
                    )}
                  </td>
                  <td className="px-3 py-3">
                    {item.before ? (
                      <>
                        <StatusLabel status={item.before.status} short />
                        <span className="tnum block text-meta text-ink-muted">{pct(item.before.completeness)}</span>
                      </>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td className="px-1 py-3 text-slate" aria-hidden="true">
                    <ArrowRight size={14} />
                  </td>
                  <td className="px-3 py-3">
                    {item.after ? (
                      <>
                        <StatusLabel status={item.after.status} short />
                        <span className="tnum block text-meta text-ink-muted">{pct(item.after.completeness)}</span>
                      </>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td className="px-3 py-3 text-ink-muted">
                    {item.element_changes.length ? (
                      <ul className="space-y-0.5">
                        {item.element_changes.map((c) => (
                          <li key={c.key}>
                            <span className="font-mono text-[0.72rem] text-ink">{c.key}</span>: {c.before ?? "not checked"} →{" "}
                            {c.after ?? "not checked"}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <span>
                        {item.evidence_added.length ? `+${item.evidence_added.length} evidence ` : ""}
                        {item.evidence_removed.length ? `−${item.evidence_removed.length} evidence` : ""}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <ul className="flex flex-wrap gap-1">
                      {item.causes.map((c) => (
                        <li key={c} className="rounded-[2px] bg-shade px-1.5 py-0.5 text-meta text-ink">
                          {c}
                        </li>
                      ))}
                    </ul>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="text-ui-sm text-ink-muted">No findings changed between these runs.</p>
      )}
    </div>
  );
}

export function HistoryScreen() {
  const companyId = useCompanyId();
  const { data: runs, error } = useApi<Run[]>(`/companies/${companyId}/runs`);
  const completed = (runs ?? []).filter((r) => r.status === "completed");
  const [afterChoice, setAfter] = useState<string>("");
  const [beforeChoice, setBefore] = useState<string>("");
  const [expanded, setExpanded] = useState<string | null>(null);
  const after = afterChoice || completed[0]?.id || "";
  const before = beforeChoice || completed[0]?.previous_run_id || completed[1]?.id || "";

  if (error) return <div className="p-6 lg:p-8"><ErrorState error={error} /></div>;
  if (!runs) return <ScreenSkeleton />;

  return (
    <div className="px-4 py-6 sm:px-6 lg:px-8">
      <PageHeader
        title="Assessment history"
        description="Runs are never overwritten. Each one records the documents, catalogue version, rules, prompt and model that produced it, so results can be audited and compared."
      />

      {completed.length >= 2 ? (
        <Section
          className="mt-8"
          title="What changed"
          description="Compare any two runs. Changes are attributed to revised requirements, replaced documents or a different method."
        >
          <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-center">
            <Select aria-label="Earlier run" value={before} onChange={(e) => setBefore(e.target.value)} className="text-ui-sm sm:max-w-sm">
              {completed.map((r) => (
                <option key={r.id} value={r.id}>{runLabel(r)}</option>
              ))}
            </Select>
            <ArrowRight className="hidden shrink-0 text-slate sm:block" />
            <Select aria-label="Later run" value={after} onChange={(e) => setAfter(e.target.value)} className="text-ui-sm sm:max-w-sm">
              {completed.map((r) => (
                <option key={r.id} value={r.id}>{runLabel(r)}</option>
              ))}
            </Select>
          </div>
          {before && after && before !== after ? (
            <DiffView
              before={before}
              after={after}
              companyId={companyId}
              isPrevious={completed.find((r) => r.id === after)?.previous_run_id === before}
            />
          ) : (
            <Notice>Choose two different runs to compare.</Notice>
          )}
        </Section>
      ) : null}

      <Section className="mt-10" title="Runs">
        {!runs.length ? (
          <EmptyState title="No runs yet">Run an assessment from the Evidence tab. Every run is kept here.</EmptyState>
        ) : (
          <ol className="space-y-3">
            {runs.map((r) => {
              const open = expanded === r.id;
              return (
                <li key={r.id} className="rounded-sm border border-rule bg-surface">
                  <button
                    type="button"
                    onClick={() => setExpanded(open ? null : r.id)}
                    aria-expanded={open}
                    className="flex w-full flex-col gap-3 px-4 py-3 text-left lg:flex-row lg:items-center lg:justify-between"
                  >
                    <span className="min-w-0">
                      <span className="block text-ui font-medium text-ink">{r.label ?? r.requirement_set_title}</span>
                      <span className="block text-ui-sm text-ink-muted">
                        <span className="font-mono text-[0.72rem]">{r.requirement_set_id}</span> · {r.period_label} ·{" "}
                        {r.mode === "hybrid" ? `rules + model (${r.llm_model})` : "rules only"} · {dateTime(r.finished_at ?? r.created_at)}
                      </span>
                    </span>
                    {r.status === "completed" ? (
                      <StatusDistribution summary={r.summary} className="w-full lg:w-80" />
                    ) : (
                      <span className={cx("text-ui-sm", r.status === "failed" ? "text-oxide" : "text-ink-muted")}>{r.status}</span>
                    )}
                  </button>
                  {open ? (
                    <div className="grid gap-6 border-t border-rule px-4 py-4 text-ui-sm lg:grid-cols-2">
                      <div>
                        <p className="text-meta font-medium text-ink">Inputs</p>
                        <ul className="mt-1.5 space-y-1.5">
                          {(r.input_manifest.documents ?? []).map((d) => (
                            <li key={d.id}>
                              <span className="block text-ink">{d.title}</span>
                              <span className="flex items-center gap-2 text-meta text-ink-muted">
                                v{d.version} · <IdTag value={d.sha256.slice(0, 16)} label="document hash" />
                              </span>
                            </li>
                          ))}
                        </ul>
                        {r.excluded_requirements.length ? (
                          <p className="mt-3 text-meta text-ink-muted">
                            Not applicable: {r.excluded_requirements.map((e) => `${e.display_code} (${e.rationale})`).join("; ")}
                          </p>
                        ) : null}
                      </div>
                      <div>
                        <p className="text-meta font-medium text-ink">Method and cost</p>
                        <dl className="mt-1.5 grid grid-cols-[9rem_1fr] gap-y-1 text-meta">
                          <dt className="text-ink-muted">Run</dt>
                          <dd><IdTag value={r.id} label="run id" /></dd>
                          <dt className="text-ink-muted">Pipeline · rules</dt>
                          <dd className="font-mono text-[0.7rem] text-ink">{r.pipeline_version} · {r.rules_version}</dd>
                          {r.prompt_version ? (
                            <>
                              <dt className="text-ink-muted">Prompt · model</dt>
                              <dd className="font-mono text-[0.7rem] text-ink">{r.prompt_version} · {r.llm_model}</dd>
                            </>
                          ) : null}
                          <dt className="text-ink-muted">Duration</dt>
                          <dd className="tnum text-ink">{num((r.metrics.timings?.total_ms ?? 0) / 1000)} s</dd>
                          {r.metrics.llm?.calls ? (
                            <>
                              <dt className="text-ink-muted">Model calls</dt>
                              <dd className="tnum text-ink">
                                {r.metrics.llm.calls} ({r.metrics.llm.cached} cached) ·{" "}
                                {num(r.metrics.llm.prompt_tokens + r.metrics.llm.completion_tokens)} tokens
                              </dd>
                            </>
                          ) : null}
                          <dt className="text-ink-muted">Evidence base</dt>
                          <dd className="tnum text-ink">
                            {r.metrics.passages ?? 0} passages · {r.metrics.extracted_metrics ?? 0} values
                          </dd>
                        </dl>
                      </div>
                    </div>
                  ) : null}
                </li>
              );
            })}
          </ol>
        )}
      </Section>
    </div>
  );
}
