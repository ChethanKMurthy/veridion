"use client";

import Link from "next/link";
import { useParams, usePathname, useRouter, useSearchParams } from "next/navigation";
import { useMemo, useState, type FormEvent } from "react";
import { buttonClass } from "@/components/ui/button";
import { ErrorState, Notice, ScreenSkeleton, Skeleton } from "@/components/ui/feedback";
import { ArrowLeft, ChevronLeft, ChevronRight, Download, Search } from "@/components/ui/icons";
import { IdTag } from "@/components/ui/overlay";
import { StatusLabel } from "@/components/ui/status";
import { useApi, useClient, useHref } from "@/lib/api/context";
import type { DocumentInfo, Passage, PassageDetail } from "@/lib/api/types";
import { DOC_TYPES, cx, dateTime, num, unit } from "@/lib/format";
import { PageView, type Highlight } from "../page-view";

function SearchPanel({ companyId, onOpen }: { companyId: string; onOpen: (p: Passage) => void }) {
  const [q, setQ] = useState("");
  const [submitted, setSubmitted] = useState("");
  const { data, isLoading } = useApi<{ query: string; results: Passage[] }>(
    submitted.length >= 2 ? "/search" : null,
    { company_id: companyId, q: submitted },
  );
  const submit = (e: FormEvent) => {
    e.preventDefault();
    setSubmitted(q.trim());
  };
  return (
    <div>
      <form onSubmit={submit} role="search" className="relative">
        <label htmlFor="doc-search" className="sr-only">
          Search this company&apos;s documents
        </label>
        <Search size={14} className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-slate" />
        <input
          id="doc-search"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search all documents, e.g. scope 2"
          className="h-9 w-full rounded-sm border border-rule-strong bg-surface pl-8 pr-3 text-ui-sm placeholder:text-ink-muted/80 focus:border-brass-deep focus:outline-none"
        />
      </form>
      {submitted ? (
        <div className="mt-3">
          {isLoading ? (
            <Skeleton className="h-24" />
          ) : data?.results.length ? (
            <ul className="space-y-1.5">
              {data.results.map((r) => (
                <li key={r.id}>
                  <button
                    type="button"
                    onClick={() => onOpen(r)}
                    className="block w-full rounded-sm border border-rule bg-surface px-3 py-2 text-left hover:border-rule-strong"
                  >
                    <span className="text-meta text-ink-muted">
                      {r.document?.short_name}, p.{r.page}
                    </span>
                    <span className="mt-0.5 line-clamp-2 block text-ui-sm text-ink">{r.text}</span>
                    {r.match ? (
                      <span className="mt-1 block text-meta text-ink-muted">
                        Matched{" "}
                        {[...r.match.phrases.map((p) => `“${p}”`), ...r.match.terms].slice(0, 5).join(", ") || "related terms"}
                        {r.match.metrics.length ? ` · values: ${r.match.metrics.join(", ")}` : ""}
                      </span>
                    ) : null}
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-ui-sm text-ink-muted">No passages match “{submitted}”.</p>
          )}
        </div>
      ) : null}
    </div>
  );
}

function PassageInfo({ passageId }: { passageId: string }) {
  const href = useHref();
  const { companyId } = useParams<{ companyId: string }>();
  const { data } = useApi<PassageDetail>(`/passages/${passageId}`);
  if (!data) return <Skeleton className="h-28" />;
  return (
    <div className="space-y-3">
      <div className="rounded-sm border border-ink bg-surface px-3 py-2.5">
        <p className="text-meta text-ink-muted">
          {data.kind.replace("_", " ")} · {data.extraction_method === "ocr" ? `OCR, confidence ${data.confidence.toFixed(2)}` : "text layer"}
        </p>
        {data.section ? <p className="mt-0.5 text-meta text-slate">{data.section}</p> : null}
        <p className="mt-1.5 text-ui-sm leading-relaxed text-ink">{data.text}</p>
        <div className="mt-2"><IdTag value={data.id} label="evidence id" /></div>
      </div>
      {data.metrics.length ? (
        <div>
          <p className="text-meta font-medium text-ink">Values extracted</p>
          <ul className="mt-1 space-y-1">
            {data.metrics.map((m) => (
              <li key={m.id} className="flex items-baseline justify-between gap-2 text-ui-sm">
                <span className="text-ink-muted">{m.label ?? m.metric_key}</span>
                <span className="tnum text-right text-ink">
                  {num(m.value)} {unit(m.unit)} <span className="text-ink-muted">· {m.period_label ?? "period?"}</span>
                  {m.normalized_unit && m.normalized_unit !== m.unit ? (
                    <span className="block text-meta text-ink-muted">
                      = {num(m.normalized_value)} {unit(m.normalized_unit)}
                    </span>
                  ) : null}
                </span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {data.cited_by.length ? (
        <div>
          <p className="text-meta font-medium text-ink">Cited by findings</p>
          <ul className="mt-1 space-y-1">
            {data.cited_by.slice(0, 6).map((c) => (
              <li key={`${c.finding_id}-${c.role}`}>
                <Link
                  href={href(`/companies/${companyId}/evidence?run=${c.run_id}&finding=${c.finding_id}`)}
                  className="flex items-center justify-between gap-2 text-ui-sm hover:underline"
                >
                  <span className="font-mono text-[0.7rem] text-ink">{c.requirement_code}</span>
                  <span className="text-meta text-ink-muted">{c.role}</span>
                  <StatusLabel status={c.status} short className="text-meta" />
                </Link>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

export function DocumentViewerScreen() {
  const { companyId, documentId } = useParams<{ companyId: string; documentId: string }>();
  const search = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const client = useClient();
  const href = useHref();
  const { data: doc, error } = useApi<DocumentInfo>(`/documents/${documentId}`);
  const { data: passages } = useApi<Passage[]>(`/documents/${documentId}/passages`);
  const page = Math.max(1, Number(search.get("page") ?? 1));
  const selected = search.get("passage");

  const go = (next: { page?: number; passage?: string | null; doc?: string }) => {
    const sp = new URLSearchParams(search.toString());
    if (next.page) sp.set("page", String(next.page));
    if (next.passage === null) sp.delete("passage");
    else if (next.passage) sp.set("passage", next.passage);
    const path = next.doc && next.doc !== documentId ? pathname.replace(documentId, next.doc) : pathname;
    router.replace(`${path}?${sp.toString()}`, { scroll: false });
  };

  const onPage = useMemo(() => (passages ?? []).filter((p) => p.page === page && p.kind !== "table"), [passages, page]);
  const highlights: Highlight[] = onPage.map((p) => ({
    id: p.id,
    bbox: p.bbox,
    role: p.id === selected ? "supporting" : "related",
    label: p.text.slice(0, 100),
  }));

  if (error) return <div className="p-6 lg:p-8"><ErrorState error={error} /></div>;
  if (!doc) return <ScreenSkeleton />;

  const pages = doc.page_count ?? 1;
  const fileUrl = client.fileUrl(doc.id);

  return (
    <div className="px-4 py-5 sm:px-6 lg:px-8">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <Link href={href(`/companies/${companyId}/documents`)} className="inline-flex items-center gap-1.5 text-ui-sm text-ink-muted hover:text-ink">
            <ArrowLeft size={14} /> Documents
          </Link>
          <h2 className="mt-2 text-[1.2rem] font-semibold text-ink">{doc.title}</h2>
          <p className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-ui-sm text-ink-muted">
            <span>{DOC_TYPES[doc.doc_type] ?? doc.doc_type}</span>
            <span>{doc.period_label ?? "No period"}</span>
            <span>Version {doc.version}</span>
            <span>Processed {dateTime(doc.processed_at)}</span>
            <IdTag value={doc.sha256} label="SHA-256" className="max-w-[12rem]" />
          </p>
        </div>
        {fileUrl ? (
          <a href={fileUrl} target="_blank" rel="noreferrer" className={buttonClass("secondary", "sm")}>
            <Download size={14} /> Original PDF
          </a>
        ) : null}
      </div>

      {doc.superseded_at ? (
        <Notice tone="warning" className="mt-4" title="A newer version of this document exists">
          This version was replaced on {dateTime(doc.superseded_at)}. Findings that cite it are kept for audit.
        </Notice>
      ) : null}
      {doc.stats.warnings?.length ? (
        <Notice tone="warning" className="mt-4">
          {doc.stats.warnings.join(" ")}
        </Notice>
      ) : null}

      <div className="mt-5 grid gap-6 xl:grid-cols-[minmax(0,1fr)_22rem]">
        <div className="min-w-0">
          <div className="mb-3 flex items-center justify-between gap-3">
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={() => go({ page: Math.max(1, page - 1), passage: null })}
                disabled={page <= 1}
                aria-label="Previous page"
                className="inline-flex size-8 items-center justify-center rounded-sm text-ink-muted hover:bg-shade disabled:opacity-40"
              >
                <ChevronLeft />
              </button>
              <span className="tnum px-1 text-ui-sm text-ink">
                Page {page} of {pages}
              </span>
              <button
                type="button"
                onClick={() => go({ page: Math.min(pages, page + 1), passage: null })}
                disabled={page >= pages}
                aria-label="Next page"
                className="inline-flex size-8 items-center justify-center rounded-sm text-ink-muted hover:bg-shade disabled:opacity-40"
              >
                <ChevronRight />
              </button>
            </div>
            <div className="flex max-w-full gap-1 overflow-x-auto no-scrollbar" role="tablist" aria-label="Pages">
              {Array.from({ length: pages }, (_, i) => i + 1).map((n) => (
                <button
                  key={n}
                  role="tab"
                  aria-selected={n === page}
                  onClick={() => go({ page: n, passage: null })}
                  className={cx(
                    "tnum inline-flex h-7 min-w-7 items-center justify-center rounded-sm px-1.5 text-meta",
                    n === page ? "bg-obsidian text-on-dark" : "text-ink-muted hover:bg-shade",
                    doc.ocr_pages.includes(n) && n !== page && "underline decoration-dotted underline-offset-4",
                  )}
                  title={doc.ocr_pages.includes(n) ? "Read by OCR" : undefined}
                >
                  {n}
                </button>
              ))}
            </div>
          </div>
          <div className="mx-auto max-w-[760px]">
            <PageView
              documentId={doc.id}
              page={page}
              pageSize={doc.page_sizes[page - 1]}
              highlights={highlights}
              activeId={selected}
              onSelect={(id) => go({ passage: id })}
              focusActive
              alt={`${doc.title}, page ${page}`}
            />
            <p className="mt-2 text-meta text-ink-muted">
              Outlined regions are the passages Veridion extracted from this page. Select one to see its values and the findings
              that cite it.
            </p>
          </div>
        </div>

        <aside className="space-y-6">
          <SearchPanel
            companyId={companyId}
            onOpen={(p) =>
              p.document_id === documentId
                ? go({ page: p.page, passage: p.id })
                : router.replace(href(`/companies/${companyId}/documents/${p.document_id}?page=${p.page}&passage=${p.id}`))
            }
          />
          {selected ? (
            <PassageInfo passageId={selected} />
          ) : (
            <div>
              <p className="text-meta font-medium text-ink">Passages on this page</p>
              <ul className="mt-1.5 space-y-1">
                {onPage.map((p) => (
                  <li key={p.id}>
                    <button
                      type="button"
                      onClick={() => go({ passage: p.id })}
                      className="block w-full rounded-sm px-2 py-1.5 text-left text-ui-sm hover:bg-shade"
                    >
                      <span className="text-meta text-slate">{p.kind.replace("_", " ")}</span>
                      <span className="line-clamp-2 block text-ink">{p.text}</span>
                    </button>
                  </li>
                ))}
                {!onPage.length ? <li className="text-ui-sm text-ink-muted">No text was extracted from this page.</li> : null}
              </ul>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
