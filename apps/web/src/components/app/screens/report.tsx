"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { Button, buttonClass } from "@/components/ui/button";
import { ErrorState, ScreenSkeleton } from "@/components/ui/feedback";
import { ArrowLeft, Download, Printer } from "@/components/ui/icons";
import { StatusLabel } from "@/components/ui/status";
import { useApi, useClient, useHref } from "@/lib/api/context";
import type { Report } from "@/lib/api/types";
import { STATUS, STATUS_ORDER, date, dateTime, pct } from "@/lib/format";
import { StatusDistribution } from "./company-overview";

export function ReportScreen() {
  const { runId } = useParams<{ runId: string }>();
  const client = useClient();
  const href = useHref();
  const { data, error } = useApi<Report>(`/runs/${runId}/report`);

  if (error) return <div className="p-6 lg:p-8"><ErrorState error={error} /></div>;
  if (!data) return <ScreenSkeleton />;

  const { company, run, requirement_set: rs } = data;
  const docs = run.input_manifest.documents ?? [];

  return (
    <div className="px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto mb-5 flex max-w-[860px] flex-wrap items-center justify-between gap-3 print-hidden">
        <Link href={href(`/companies/${company.id}/evidence?run=${run.id}`)} className="inline-flex items-center gap-1.5 text-ui-sm text-ink-muted hover:text-ink">
          <ArrowLeft size={14} /> Back to evidence
        </Link>
        <div className="flex flex-wrap gap-2">
          <Button size="sm" variant="primary" icon={<Printer size={14} />} onClick={() => window.print()}>
            Print or save as PDF
          </Button>
          {(["json", "csv", "md"] as const).map((f) => (
            <a key={f} href={client.exportUrl(run.id, f)} download className={buttonClass("secondary", "sm")}>
              <Download size={14} /> {f === "json" ? "Evidence package (JSON)" : f.toUpperCase()}
            </a>
          ))}
        </div>
      </div>

      <article className="mx-auto max-w-[860px] bg-surface px-6 py-10 shadow-[0_0_0_1px_var(--color-rule)] sm:px-12 print:max-w-none print:px-0 print:py-0 print:shadow-none">
        <header className="border-b border-rule pb-8">
          <p className="text-ui-sm text-ink-muted">Evidence assessment</p>
          <h1 className="mt-2 font-display text-[2.6rem] leading-[1.05] tracking-[-0.01em] text-ink">{company.name}</h1>
          <p className="mt-3 text-ui text-ink-muted">
            {rs.title} · catalogue v{rs.version} · period {run.period_label} ({date(run.period_start)} – {date(run.period_end)})
          </p>
          <dl className="mt-6 grid grid-cols-2 gap-x-8 gap-y-2 text-ui-sm sm:grid-cols-4">
            <div>
              <dt className="text-meta text-ink-muted">Method</dt>
              <dd className="text-ink">{run.mode === "hybrid" ? `Rules + model` : "Rules only"}</dd>
            </div>
            <div>
              <dt className="text-meta text-ink-muted">Completed</dt>
              <dd className="text-ink">{dateTime(run.finished_at)}</dd>
            </div>
            <div>
              <dt className="text-meta text-ink-muted">Documents</dt>
              <dd className="tnum text-ink">{docs.length}</dd>
            </div>
            <div>
              <dt className="text-meta text-ink-muted">Run</dt>
              <dd className="truncate font-mono text-[0.72rem] text-ink">{run.id}</dd>
            </div>
          </dl>
          {company.is_sample ? (
            <p className="mt-6 rounded-sm bg-brass-tint px-3 py-2 text-ui-sm text-ink">
              Fictional sample company. The documents and figures were invented to demonstrate the platform.
            </p>
          ) : null}
        </header>

        <section className="py-8 print-avoid-break">
          <h2 className="font-display text-[1.6rem] text-ink">Summary</h2>
          <StatusDistribution summary={run.summary} className="mt-4" />
          <table className="mt-6 w-full text-left text-ui-sm">
            <thead>
              <tr className="border-b border-rule text-meta text-ink-muted">
                <th className="py-2 pr-3 font-medium">Requirement</th>
                <th className="py-2 pr-3 font-medium">Status</th>
                <th className="py-2 pr-3 text-right font-medium">Completeness</th>
                <th className="py-2 text-right font-medium">Priority</th>
              </tr>
            </thead>
            <tbody>
              {data.findings.map((f) => (
                <tr key={f.id} className="border-b border-rule">
                  <td className="py-2 pr-3">
                    <span className="font-mono text-[0.72rem] text-ink-muted">{f.display_code}</span> <span className="text-ink">{f.title}</span>
                  </td>
                  <td className="py-2 pr-3"><StatusLabel status={f.review.effective_status} short /></td>
                  <td className="tnum py-2 pr-3 text-right">{pct(f.completeness)}</td>
                  <td className="tnum py-2 text-right">{(f.priority.P ?? 0).toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section className="border-t border-rule py-8">
          <h2 className="font-display text-[1.6rem] text-ink">Findings</h2>
          <div className="mt-2 space-y-8">
            {data.findings.map((f) => {
              const trail = data.trails[f.id];
              const evidence = (trail?.evidence ?? []).filter((e) => e.role !== "related").slice(0, 4);
              return (
                <div key={f.id} className="print-avoid-break border-b border-rule pb-6 last:border-0">
                  <div className="flex flex-wrap items-baseline justify-between gap-2 pt-4">
                    <h3 className="text-[1.05rem] font-semibold text-ink">
                      <span className="mr-2 font-mono text-[0.78rem] text-ink-muted">{f.display_code}</span>
                      {f.title}
                    </h3>
                    <StatusLabel status={f.review.effective_status} />
                  </div>
                  <p className="mt-1 text-meta text-ink-muted">
                    Completeness {pct(f.completeness)} · confidence {f.confidence.toFixed(2)} ·{" "}
                    {f.review.state === "unreviewed" ? "not yet reviewed" : `${f.review.state} by ${f.review.latest?.reviewer_name ?? "a reviewer"}`}
                  </p>
                  <p className="mt-3 text-ui leading-relaxed text-ink">{f.rationale.replace(/\s*\[?\(?ev_[0-9a-f]{20}\)?\]?/g, "")}</p>
                  {evidence.length ? (
                    <ul className="mt-3 space-y-2">
                      {evidence.map((e) => (
                        <li key={`${e.passage.id}-${e.role}`} className="text-ui-sm">
                          <span className="text-meta text-ink-muted">
                            {e.role === "conflicting" ? "Conflicting" : "Evidence"} · {e.passage.document?.short_name}, p.{e.passage.page}
                          </span>
                          <blockquote className="mt-0.5 border-l border-rule-strong pl-3 font-serif text-[0.92rem] leading-relaxed text-ink">
                            {e.passage.text}
                          </blockquote>
                        </li>
                      ))}
                    </ul>
                  ) : null}
                  {f.missing_elements.length ? (
                    <p className="mt-3 text-ui-sm text-ink-muted">
                      <span className="font-medium text-ink">Missing:</span> {f.missing_elements.join("; ")}.
                    </p>
                  ) : null}
                </div>
              );
            })}
          </div>
        </section>

        {data.actions.length ? (
          <section className="border-t border-rule py-8 print-break">
            <h2 className="font-display text-[1.6rem] text-ink">Recommended actions</h2>
            <ol className="mt-4 space-y-4">
              {data.actions.map((a, i) => (
                <li key={a.id} className="print-avoid-break grid grid-cols-[2rem_1fr] gap-x-2">
                  <span className="tnum pt-0.5 text-ui-sm text-ink-muted">{i + 1}.</span>
                  <div>
                    <p className="text-ui font-medium text-ink">{a.title}</p>
                    <p className="mt-0.5 text-ui-sm leading-relaxed text-ink-muted">{a.detail}</p>
                    <p className="mt-1 text-meta text-ink-muted">
                      {a.requirement_code} · priority {a.priority_score.toFixed(2)} · {a.effort} effort
                      {a.owner ? ` · owner ${a.owner}` : ""}
                      {a.due_date ? ` · due ${date(a.due_date)}` : ""}
                    </p>
                  </div>
                </li>
              ))}
            </ol>
          </section>
        ) : null}

        <section className="border-t border-rule py-8 text-ui-sm">
          <h2 className="font-display text-[1.6rem] text-ink">Method and limitations</h2>
          <dl className="mt-4 space-y-2">
            {STATUS_ORDER.map((s) => (
              <div key={s} className="grid gap-1 sm:grid-cols-[13rem_1fr]">
                <dt><StatusLabel status={s} /></dt>
                <dd className="text-ink-muted">{STATUS[s].description}</dd>
              </div>
            ))}
          </dl>
          <p className="mt-5 leading-relaxed text-ink-muted">
            Completeness is the weighted share of a requirement&apos;s elements that are evidenced: C = Σ wᵢsᵢ / Σ wᵢ. It is an
            internal evidence-completeness measure, not a compliance score. Priority is importance × gap × urgency.
          </p>
          <ul className="mt-4 list-disc space-y-1.5 pl-5 text-ink-muted">
            {data.limitations.map((l) => (
              <li key={l}>{l}</li>
            ))}
          </ul>
          <h3 className="mt-6 font-semibold text-ink">Provenance</h3>
          <ul className="mt-2 space-y-1 text-meta text-ink-muted [overflow-wrap:anywhere]">
            {docs.map((d) => (
              <li key={d.id}>
                {d.title} · v{d.version} · <span className="font-mono break-all">{d.sha256}</span>
              </li>
            ))}
            <li>
              Catalogue <span className="font-mono">{rs.id}</span> · <span className="font-mono">{rs.content_hash.slice(0, 16)}</span>
            </li>
            <li>
              Engine <span className="font-mono">{[run.pipeline_version, run.extraction_version, run.rules_version, run.prompt_version].filter(Boolean).join(" · ")}</span>
              {run.llm_model ? <> · model <span className="font-mono">{run.llm_model}</span></> : null}
            </li>
            <li>Generated {dateTime(data.generated_at)} by {data.generator}</li>
          </ul>
        </section>
      </article>
    </div>
  );
}
