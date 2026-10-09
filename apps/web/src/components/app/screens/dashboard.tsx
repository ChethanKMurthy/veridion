"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import { buttonClass } from "@/components/ui/button";
import { ErrorState, ScreenSkeleton } from "@/components/ui/feedback";
import { ArrowRight } from "@/components/ui/icons";
import { StatusLabel } from "@/components/ui/status";
import { useApi, useHref } from "@/lib/api/context";
import type { Dashboard, Me } from "@/lib/api/types";
import { DOC_TYPES, cx, num, relative, unit } from "@/lib/format";
import { PageHeader } from "../shell";
import { StatusDistribution } from "./company-overview";

function Panel({ title, description, children, action, className }: { title: string; description?: string; children: ReactNode; action?: ReactNode; className?: string }) {
  return (
    <section className={cx("min-w-0 rounded-sm border border-rule bg-surface", className)}>
      <div className="flex items-start justify-between gap-3 border-b border-rule px-4 py-3">
        <div>
          <h2 className="text-ui font-semibold text-ink">{title}</h2>
          {description ? <p className="mt-0.5 text-ui-sm text-ink-muted">{description}</p> : null}
        </div>
        {action}
      </div>
      <div className="px-4 py-2">{children}</div>
    </section>
  );
}

function Empty({ children }: { children: ReactNode }) {
  return <p className="py-4 text-ui-sm text-ink-muted">{children}</p>;
}

function Onboarding() {
  const href = useHref();
  const steps = [
    ["Add a company", "Create the company you are assessing, with its financial year end.", href("/companies")],
    ["Upload its disclosures", "Annual report, sustainability report and policies, as PDF.", href("/companies")],
    ["Run an assessment", "Choose a versioned requirement catalogue and a reporting period.", href("/companies")],
    ["Review the evidence", "Open each finding, follow the trail to the source page, and record your decision.", href("/companies")],
  ];
  return (
    <div className="mt-8 rounded-sm border border-rule bg-surface p-6">
      <h2 className="font-display text-[1.6rem] text-ink">Set up your first assessment</h2>
      <p className="mt-1 max-w-2xl text-ui text-ink-muted">
        Four steps from a folder of PDFs to findings you can defend, each linked to the page it came from.
      </p>
      <ol className="mt-6 grid gap-px overflow-hidden rounded-sm border border-rule bg-rule md:grid-cols-4">
        {steps.map(([title, detail, link], i) => (
          <li key={title} className="bg-surface p-4">
            <span className="tnum inline-flex size-6 items-center justify-center rounded-full border border-ink text-meta">{i + 1}</span>
            <p className="mt-3 text-ui font-medium text-ink">{title}</p>
            <p className="mt-1 text-ui-sm text-ink-muted">{detail}</p>
            {i === 0 ? (
              <Link href={link} className={cx(buttonClass("primary", "sm"), "mt-4")}>
                Add a company
              </Link>
            ) : null}
          </li>
        ))}
      </ol>
      <p className="mt-4 text-ui-sm text-ink-muted">
        Want to see a finished workspace first?{" "}
        <Link href="/demo" className="font-medium text-ink underline underline-offset-2">
          Open the interactive demo
        </Link>
        .
      </p>
    </div>
  );
}

export function DashboardScreen() {
  const href = useHref();
  const { data: me } = useApi<Me>("/auth/me");
  const { data, error, mutate } = useApi<Dashboard>("/dashboard");
  if (error) return <div className="p-6 lg:p-8"><ErrorState error={error} retry={() => mutate()} /></div>;
  if (!data) return <ScreenSkeleton />;

  const c = data.counts;
  const finding = (companyId: string, runId: string, findingId: string) =>
    href(`/companies/${companyId}/evidence?run=${runId}&finding=${findingId}`);

  return (
    <div className="px-4 py-6 sm:px-6 lg:px-8">
      <PageHeader
        title={me ? `Good to see you, ${me.user.name.split(" ")[0]}` : "Overview"}
        description={
          <span className="tnum">
            {c.companies} {c.companies === 1 ? "company" : "companies"} · {c.documents} documents · {c.runs} assessment runs ·{" "}
            {c.open_actions} open actions
          </span>
        }
        actions={
          <Link href={href("/companies")} className={buttonClass("secondary", "sm")}>
            All companies
          </Link>
        }
      />

      {c.companies === 0 ? (
        <Onboarding />
      ) : (
        <div className="mt-8 grid gap-5 xl:grid-cols-2">
          <Panel title="Needs your review" description="Findings the system could not resolve on its own.">
            {data.review_queue.length ? (
              <ul className="divide-y divide-rule">
                {data.review_queue.map((f) => (
                  <li key={f.finding_id}>
                    <Link href={finding(f.company_id, f.run_id, f.finding_id)} className="group block py-2.5">
                      <span className="flex items-center justify-between gap-3">
                        <span className="text-ui-sm text-ink group-hover:underline">
                          <span className="mr-1.5 font-mono text-[0.72rem] text-ink-muted">{f.display_code}</span>
                          {f.title}
                        </span>
                        <StatusLabel status={f.status} short className="text-meta" />
                      </span>
                      <span className="mt-0.5 block text-meta text-ink-muted">
                        {f.company} · {f.reasons[0] ?? "Review the evidence trail"}
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            ) : (
              <Empty>Nothing is waiting for review.</Empty>
            )}
          </Panel>

          <Panel title="Unresolved contradictions" description="Sources that disagree on a material value.">
            {data.contradictions.length ? (
              <ul className="divide-y divide-rule">
                {data.contradictions.map((f) => (
                  <li key={f.finding_id} className="py-2.5">
                    <Link href={finding(f.company_id, f.run_id, f.finding_id)} className="group block">
                      <span className="text-ui-sm text-ink group-hover:underline">
                        <span className="mr-1.5 font-mono text-[0.72rem] text-ink-muted">{f.display_code}</span>
                        {f.company}
                      </span>
                      {f.conflicts.map((cf) => (
                        <span key={cf.metric_key} className="mt-1 block text-meta text-ink-muted">
                          {cf.label} {cf.period}:{" "}
                          <span className="tnum text-ink">
                            {num(cf.low.value)} {unit(cf.low.unit)}
                          </span>{" "}
                          ({cf.low.source}) vs{" "}
                          <span className="tnum text-ink">
                            {num(cf.high.value)} {unit(cf.high.unit)}
                          </span>{" "}
                          ({cf.high.source}) · {(cf.relative_difference * 100).toFixed(1)}% apart
                        </span>
                      ))}
                    </Link>
                  </li>
                ))}
              </ul>
            ) : (
              <Empty>No conflicting figures in the latest runs.</Empty>
            )}
          </Panel>

          <Panel title="Material gaps" description="Open actions ranked by importance × gap × urgency.">
            {data.material_gaps.length ? (
              <ol className="divide-y divide-rule">
                {data.material_gaps.map((a) => (
                  <li key={a.id}>
                    <Link href={href(`/companies/${a.company_id}/actions`)} className="group grid grid-cols-[3rem_1fr] gap-2 py-2.5">
                      <span className="tnum text-ui font-semibold text-ink">{num(a.priority_score)}</span>
                      <span className="min-w-0">
                        <span className="block text-ui-sm text-ink group-hover:underline">{a.title}</span>
                        <span className="block text-meta text-ink-muted">
                          {a.company} · {a.requirement_code} · {a.owner ? a.owner : "unassigned"} · {a.status.replace("_", " ")}
                        </span>
                      </span>
                    </Link>
                  </li>
                ))}
              </ol>
            ) : (
              <Empty>No open actions.</Empty>
            )}
          </Panel>

          <Panel title="Changes since the previous run" description="Why findings moved between assessments.">
            {data.changes.length ? (
              <ul className="divide-y divide-rule">
                {data.changes.map((ch) => (
                  <li key={ch.run_id} className="py-2.5">
                    <p className="text-ui-sm text-ink">
                      {ch.company}: {ch.summary}
                    </p>
                    <ul className="mt-1 space-y-0.5">
                      {ch.items.map((it) => (
                        <li key={it.requirement_code} className="flex flex-wrap items-center gap-x-2 text-meta text-ink-muted">
                          <span className="font-mono text-ink">{it.requirement_code}</span>
                          {it.before ? <StatusLabel status={it.before.status} short /> : "new"}
                          <ArrowRight size={12} />
                          {it.after ? <StatusLabel status={it.after.status} short /> : "removed"}
                          <span>· {it.causes.join(", ")}</span>
                        </li>
                      ))}
                    </ul>
                    <Link href={href(`/companies/${ch.company_id}/history`)} className="mt-1.5 inline-block text-meta font-medium text-ink hover:underline">
                      Compare runs
                    </Link>
                  </li>
                ))}
              </ul>
            ) : (
              <Empty>Changes appear after a company has been assessed more than once.</Empty>
            )}
          </Panel>

          <Panel title="Recent assessment runs">
            <ul className="divide-y divide-rule">
              {data.recent_runs.map((r) => (
                <li key={r.id} className="py-2.5">
                  <Link href={href(`/companies/${r.company_id}/evidence?run=${r.id}`)} className="group block">
                    <span className="flex flex-wrap items-baseline justify-between gap-2">
                      <span className="text-ui-sm text-ink group-hover:underline">{r.company}</span>
                      <span className="text-meta text-ink-muted">{relative(r.finished_at ?? r.created_at)}</span>
                    </span>
                    <span className="block text-meta text-ink-muted">
                      <span className="font-mono">{r.requirement_set_id}</span> · {r.mode === "hybrid" ? "rules + model" : "rules"}
                    </span>
                    {r.status === "completed" ? <StatusDistribution summary={r.summary} className="mt-2" /> : null}
                  </Link>
                </li>
              ))}
            </ul>
          </Panel>

          <div className="space-y-5">
            <Panel title="Recently added documents">
              <ul className="divide-y divide-rule">
                {data.recent_documents.map((d) => (
                  <li key={d.id}>
                    <Link href={href(`/companies/${d.company_id}/documents/${d.id}`)} className="group block py-2.5">
                      <span className="block truncate text-ui-sm text-ink group-hover:underline">{d.title}</span>
                      <span className="text-meta text-ink-muted">
                        {d.company} · {DOC_TYPES[d.doc_type] ?? d.doc_type} · {d.page_count ?? "—"} pages · {relative(d.created_at)}
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            </Panel>
            {data.peer_coverage.length ? (
              <Panel title="Peer comparisons" description="How much of each metric the peer group discloses.">
                {data.peer_coverage.map((pc) => (
                  <div key={pc.company_id} className="py-2">
                    <Link href={href(`/companies/${pc.company_id}/peers`)} className="text-ui-sm font-medium text-ink hover:underline">
                      {pc.company} vs {pc.peers.join(", ")}
                    </Link>
                    <ul className="mt-1.5 grid grid-cols-[1fr_auto] gap-x-4 gap-y-0.5 text-meta">
                      {pc.metrics.map((m) => (
                        <li key={m.label} className="contents">
                          <span className="text-ink-muted">{m.label}</span>
                          <span className="tnum text-ink">
                            {m.coverage} <span className="text-ink-muted">· {m.comparability.split(" —")[0]}</span>
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </Panel>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}
