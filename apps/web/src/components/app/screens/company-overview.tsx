"use client";

import Link from "next/link";
import { buttonClass } from "@/components/ui/button";
import { EmptyState, ErrorState, ScreenSkeleton } from "@/components/ui/feedback";
import { ArrowRight } from "@/components/ui/icons";
import { StatusGlyph, StatusLabel } from "@/components/ui/status";
import { useApi, useHref } from "@/lib/api/context";
import type { Overview, RunSummary, Status } from "@/lib/api/types";
import { DOC_TYPES, STATUS, STATUS_ORDER, cx, date, num, pct, plural, relative, signedPct, unit } from "@/lib/format";
import { Section } from "../shell";
import { useCompanyId } from "../company-frame";

const BAR_TONE: Record<Status, string> = {
  supported: "bg-forest",
  partially_supported: "bg-brass",
  not_found: "bg-rule-strong",
  conflicting: "bg-oxide",
  human_review: "bg-ink",
};

export function StatusDistribution({ summary, className }: { summary: RunSummary; className?: string }) {
  const counts = summary.counts ?? {};
  const total = Object.values(counts).reduce((a, b) => a + (b ?? 0), 0) || 1;
  const ordered = STATUS_ORDER.filter((s) => counts[s]);
  return (
    <div className={className}>
      <div className="flex h-2 overflow-hidden rounded-[1px] bg-shade" aria-hidden="true">
        {ordered.map((s) => (
          <span key={s} className={cx("h-full first:rounded-l-[1px]", BAR_TONE[s])} style={{ width: `${((counts[s] ?? 0) / total) * 100}%` }} />
        ))}
      </div>
      <ul className="mt-2.5 flex flex-wrap gap-x-4 gap-y-1.5 text-ui-sm">
        {ordered.map((s) => (
          <li key={s} className="flex items-center gap-1.5">
            <StatusGlyph status={s} />
            <span className="text-ink-muted">{STATUS[s].short}</span>
            <span className="tnum font-medium text-ink">{counts[s]}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function CompanyOverviewScreen() {
  const companyId = useCompanyId();
  const href = useHref();
  const { data, error, mutate } = useApi<Overview>(`/companies/${companyId}/overview`);
  if (error) return <div className="p-6 lg:p-8"><ErrorState error={error} retry={() => mutate()} /></div>;
  if (!data) return <ScreenSkeleton />;

  const base = href(`/companies/${companyId}`);
  const cov = data.coverage;
  const latest = data.latest_run;
  const sourceHref = (documentId: string, page: number, passageId: string) =>
    `${base}/documents/${documentId}?page=${page}&passage=${passageId}`;

  if (!cov.documents) {
    return (
      <div className="px-4 py-8 sm:px-6 lg:px-8">
        <EmptyState
          title="Start with this company's disclosures"
          action={
            <Link href={`${base}/documents`} className={buttonClass("primary", "md")}>
              Upload documents
            </Link>
          }
        >
          Upload an annual report, sustainability report or policy (PDF). Veridion extracts passages, tables and values with page
          references, then assesses them against a requirement catalogue.
        </EmptyState>
      </div>
    );
  }

  return (
    <div className="px-4 py-6 sm:px-6 lg:px-8">
      <p className="flex flex-wrap gap-x-5 gap-y-1 text-ui-sm text-ink-muted">
        <span>
          <span className="tnum font-medium text-ink">{cov.documents}</span> {cov.documents === 1 ? "document" : "documents"}
        </span>
        <span>
          <span className="tnum font-medium text-ink">{cov.pages}</span> pages
        </span>
        <span>Periods {cov.periods.join(", ") || "—"}</span>
        <span>
          <span className="tnum font-medium text-ink">{cov.metrics}</span> values extracted
        </span>
        {cov.ocr_pages ? <span>{plural(cov.ocr_pages, "page")} read by OCR</span> : null}
      </p>

      <div className="mt-6 grid gap-8 xl:grid-cols-[minmax(0,1fr)_20rem]">
        <div className="min-w-0 space-y-10">
          <Section
            title="Key disclosures"
            description="The most confident value for each metric in the latest period, with the prior period where disclosed."
          >
            {data.key_disclosures.length ? (
              <div className="overflow-x-auto rounded-sm border border-rule bg-surface scrollbar-quiet">
                <table className="w-full min-w-[640px] text-left text-ui-sm">
                  <thead>
                    <tr className="border-b border-rule text-meta text-ink-muted">
                      <th scope="col" className="px-4 py-2.5 font-medium">Metric</th>
                      <th scope="col" className="px-3 py-2.5 text-right font-medium">Value</th>
                      <th scope="col" className="px-3 py-2.5 font-medium">Period</th>
                      <th scope="col" className="px-3 py-2.5 text-right font-medium">Prior period</th>
                      <th scope="col" className="px-3 py-2.5 text-right font-medium">Change</th>
                      <th scope="col" className="px-4 py-2.5 font-medium">Source</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.key_disclosures.map((k) => (
                      <tr key={k.metric_key} className="border-b border-rule last:border-0">
                        <td className="px-4 py-2.5 text-ink">
                          {k.label}
                          {k.sources > 1 ? <span className="ml-1.5 text-meta text-ink-muted">{k.sources} sources</span> : null}
                        </td>
                        <td className="tnum px-3 py-2.5 text-right font-medium text-ink">
                          {num(k.current.value)} <span className="font-normal text-ink-muted">{unit(k.current.unit)}</span>
                        </td>
                        <td className="px-3 py-2.5 text-ink-muted">{k.current.period_label ?? "—"}</td>
                        <td className="tnum px-3 py-2.5 text-right text-ink-muted">
                          {k.prior ? `${num(k.prior.value)} ${unit(k.prior.unit)}` : "Not disclosed"}
                        </td>
                        <td className="tnum px-3 py-2.5 text-right text-ink">{k.change === null ? "—" : signedPct(k.change)}</td>
                        <td className="px-4 py-2.5">
                          <Link
                            href={sourceHref(k.current.document_id, k.current.page, k.current.passage_id)}
                            className="text-ink underline decoration-rule-strong underline-offset-2 hover:decoration-ink"
                          >
                            {k.current.source}
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <EmptyState title="No values extracted yet">
                Values appear here once documents finish processing. Tables with year columns produce the most reliable figures.
              </EmptyState>
            )}
          </Section>

          <Section
            title="Assessment"
            description={latest ? `${latest.requirement_set_title} · v${latest.requirement_set_id.split("@")[1]} · ${latest.period_label}` : undefined}
            actions={
              latest ? (
                <Link href={`${base}/evidence`} className={buttonClass("secondary", "sm")}>
                  Open Evidence Explorer <ArrowRight size={14} />
                </Link>
              ) : null
            }
          >
            {latest ? (
              <div className="rounded-sm border border-rule bg-surface p-4">
                <StatusDistribution summary={latest.summary} />
                <p className="mt-3 text-meta text-ink-muted">
                  {latest.mode === "hybrid" ? `Rules + model (${latest.llm_model})` : "Deterministic rules"} · completed{" "}
                  {relative(latest.finished_at)} · average evidence completeness {pct(latest.summary.average_completeness ?? 0)}
                </p>
              </div>
            ) : (
              <EmptyState
                title="Not assessed yet"
                action={
                  <Link href={`${base}/evidence`} className={buttonClass("primary", "sm")}>
                    Run an assessment
                  </Link>
                }
              >
                Choose a requirement catalogue to see which disclosures are supported, partial, missing or conflicting.
              </EmptyState>
            )}
          </Section>

          {data.runs.length > 1 ? (
            <Section title="Assessment history" actions={<Link href={`${base}/history`} className="text-ui-sm font-medium text-ink hover:underline">Compare runs</Link>}>
              <ol className="divide-y divide-rule rounded-sm border border-rule bg-surface">
                {data.runs.map((r) => (
                  <li key={r.id} className="flex flex-wrap items-center justify-between gap-3 px-4 py-2.5 text-ui-sm">
                    <span className="min-w-0">
                      <span className="text-ink">{r.label ?? r.requirement_set_title}</span>
                      <span className="ml-2 font-mono text-[0.7rem] text-ink-muted">{r.requirement_set_id}</span>
                    </span>
                    <span className="flex items-center gap-4 text-ink-muted">
                      <span>{r.mode === "hybrid" ? "Rules + model" : "Rules"}</span>
                      <span>{date(r.finished_at ?? r.created_at)}</span>
                      <Link href={`${base}/evidence?run=${r.id}`} className="font-medium text-ink hover:underline">
                        View
                      </Link>
                    </span>
                  </li>
                ))}
              </ol>
            </Section>
          ) : null}
        </div>

        <aside className="space-y-10">
          <Section title="Unresolved questions">
            {data.unresolved.length ? (
              <ul className="space-y-2">
                {data.unresolved.map((u) => (
                  <li key={u.finding_id}>
                    <Link
                      href={`${base}/evidence?finding=${u.finding_id}`}
                      className="block rounded-sm border border-rule bg-surface px-3 py-2.5 transition-colors hover:border-rule-strong"
                    >
                      <span className="flex items-center justify-between gap-2">
                        <span className="font-mono text-[0.7rem] text-ink-muted">{u.requirement_code}</span>
                        <StatusLabel status={u.status} short className="text-meta" />
                      </span>
                      <span className="mt-1 line-clamp-3 block text-ui-sm text-ink">{u.reasons[0] ?? STATUS[u.status].description}</span>
                    </Link>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-ui-sm text-ink-muted">Nothing needs a reviewer&apos;s judgement in the latest run.</p>
            )}
          </Section>

          <Section title="Peers" actions={<Link href={`${base}/peers`} className="text-ui-sm font-medium text-ink hover:underline">Compare</Link>}>
            {data.peers.length ? (
              <ul className="space-y-1 text-ui-sm">
                {data.peers.map((p) => (
                  <li key={p.id} className="flex items-center justify-between gap-2">
                    <Link href={href(`/companies/${p.id}`)} className="truncate text-ink hover:underline">
                      {p.name}
                    </Link>
                    <span className="shrink-0 text-meta text-ink-muted">{p.fiscal_year_end === "12-31" ? "Calendar year" : `Year end ${p.fiscal_year_end}`}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-ui-sm text-ink-muted">No peers selected. Choose comparable companies on the Peers tab.</p>
            )}
          </Section>

          <Section title="Documents" actions={<Link href={`${base}/documents`} className="text-ui-sm font-medium text-ink hover:underline">Manage</Link>}>
            <ul className="space-y-2">
              {data.documents.map((d) => (
                <li key={d.id}>
                  <Link href={`${base}/documents/${d.id}`} className="group block text-ui-sm">
                    <span className="block truncate text-ink group-hover:underline">{d.title}</span>
                    <span className="text-meta text-ink-muted">
                      {DOC_TYPES[d.doc_type] ?? d.doc_type} · {d.page_count ?? "—"} pages · v{d.version}
                      {d.status !== "ready" ? ` · ${d.status}` : ""}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          </Section>
        </aside>
      </div>
    </div>
  );
}
