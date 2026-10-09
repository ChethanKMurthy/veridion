"use client";

import Link from "next/link";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { EmptyState, ErrorState, ScreenSkeleton } from "@/components/ui/feedback";
import { Select } from "@/components/ui/field";
import { Dialog, useToast } from "@/components/ui/overlay";
import { useApi, useClient, useHref, useInvalidate } from "@/lib/api/context";
import type { Benchmark, BenchmarkCell, Company } from "@/lib/api/types";
import { cx, num, unit } from "@/lib/format";
import { PageHeader } from "../shell";
import { useCompanyId } from "../company-frame";

const NOTE_LABEL: Record<string, string> = {
  missing: "Missing",
  method: "Method",
  conflict: "Conflict",
  converted: "Converted",
  ocr: "OCR",
  period: "Period",
  boundary: "Boundary",
  denominator: "Denominator",
  scope: "Scope",
};

function Sparkline({ points }: { points: { value: number | null; period_label: string }[] }) {
  const values = points.map((p) => p.value).filter((v): v is number => v !== null);
  if (values.length < 2) return <span className="text-meta text-ink-muted">—</span>;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const w = 64;
  const h = 18;
  const coords = values.map((v, i) => [(i / (values.length - 1)) * w, h - ((v - min) / (max - min || 1)) * (h - 4) - 2]);
  const change = (values[values.length - 1] - values[0]) / Math.abs(values[0] || 1);
  return (
    <span className="inline-flex items-center gap-2" title={points.map((p) => `${p.period_label}: ${num(p.value)}`).join(" · ")}>
      <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} aria-hidden="true">
        <polyline points={coords.map((c) => c.join(",")).join(" ")} fill="none" stroke="var(--color-ink-muted)" strokeWidth="1.25" />
        <circle cx={coords[coords.length - 1][0]} cy={coords[coords.length - 1][1]} r="1.8" fill="var(--color-ink)" />
      </svg>
      <span className="tnum text-meta text-ink-muted">
        {change > 0 ? "+" : change < 0 ? "−" : ""}
        {Math.abs(change * 100).toFixed(1)}% since {points[0].period_label}
      </span>
    </span>
  );
}

function PeerEditor({ open, onClose, companyId, current }: { open: boolean; onClose: () => void; companyId: string; current: string[] }) {
  const client = useClient();
  const invalidate = useInvalidate();
  const toast = useToast();
  const { data: companies } = useApi<Company[]>(open ? "/companies" : null);
  const [selected, setSelected] = useState<string[]>(current);
  const [busy, setBusy] = useState(false);
  const save = async () => {
    setBusy(true);
    try {
      await client.send("PUT", `/companies/${companyId}/peers`, { peer_ids: selected });
      await invalidate(`/companies/${companyId}`, "/companies", "/dashboard");
      toast("Peers updated", "success");
      onClose();
    } catch (err) {
      toast(err instanceof Error ? err.message : "Could not update peers", "danger");
    } finally {
      setBusy(false);
    }
  };
  return (
    <Dialog
      open={open}
      onClose={onClose}
      title="Choose peers"
      description="Compare with companies of similar activity and size. Up to ten."
      footer={
        <>
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button variant="primary" onClick={save} loading={busy}>Save peers</Button>
        </>
      }
    >
      <ul className="divide-y divide-rule">
        {(companies ?? []).filter((c) => c.id !== companyId).map((c) => (
          <li key={c.id}>
            <label className="flex items-center gap-3 py-2.5 text-ui">
              <input
                type="checkbox"
                className="size-4 accent-[var(--color-ink)]"
                checked={selected.includes(c.id)}
                onChange={(e) => setSelected((s) => (e.target.checked ? [...s, c.id] : s.filter((x) => x !== c.id)))}
              />
              <span className="flex-1 text-ink">{c.name}</span>
              <span className="text-meta text-ink-muted">{c.industry}</span>
            </label>
          </li>
        ))}
      </ul>
    </Dialog>
  );
}

export function PeersScreen() {
  const companyId = useCompanyId();
  const href = useHref();
  const client = useClient();
  const [period, setPeriod] = useState("FY2025");
  const [editing, setEditing] = useState(false);
  const { data: company } = useApi<Company>(`/companies/${companyId}`);
  const { data, error, mutate } = useApi<Benchmark>(`/companies/${companyId}/benchmark`, { period });

  if (error) return <div className="p-6 lg:p-8"><ErrorState error={error} retry={() => mutate()} /></div>;
  if (!data || !company) return <ScreenSkeleton />;

  const names = Object.fromEntries(data.companies.map((c) => [c.id, c.name]));
  const sourceHref = (cell: BenchmarkCell) =>
    `${href(`/companies/${cell.company_id}/documents/${cell.document_id}`)}?page=${cell.page}&passage=${cell.passage_id}`;

  return (
    <div className="px-4 py-6 sm:px-6 lg:px-8">
      <PageHeader
        title="Peer intelligence"
        description="Values are compared only after unit conversion, and every comparison lists what limits it. A missing value means not disclosed in the documents provided — never zero."
        actions={
          <>
            <Select aria-label="Reporting period" value={period} onChange={(e) => setPeriod(e.target.value)} className="h-8 w-28 text-ui-sm">
              {["FY2025", "FY2024", "FY2023"].map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </Select>
            {client.mode === "live" ? (
              <Button size="sm" onClick={() => setEditing(true)}>Choose peers</Button>
            ) : null}
          </>
        }
      />

      {data.companies.length < 2 ? (
        <EmptyState className="mt-6" title="Add peers to compare" action={client.mode === "live" ? <Button variant="primary" onClick={() => setEditing(true)}>Choose peers</Button> : null}>
          Pick two or three comparable companies. Veridion aligns units, flags differing fiscal periods and consolidation
          approaches, and links every value to its page.
        </EmptyState>
      ) : (
        <>
          <div className="mt-6 grid gap-px overflow-hidden rounded-sm border border-rule bg-rule sm:grid-cols-2 xl:grid-cols-3">
            {data.companies.map((c) => (
              <div key={c.id} className="bg-surface px-4 py-3">
                <p className="flex items-center gap-2 text-ui font-medium text-ink">
                  <span className={cx("inline-block size-2 rounded-full", c.is_focal ? "bg-ink" : "bg-slate")} aria-hidden="true" />
                  {c.name}
                  {c.is_focal ? <span className="text-meta font-normal text-ink-muted">focal</span> : null}
                </p>
                <dl className="mt-1.5 grid grid-cols-[5.5rem_1fr] gap-y-0.5 text-meta">
                  <dt className="text-ink-muted">Period</dt>
                  <dd className="text-ink">{c.period.description}</dd>
                  <dt className="text-ink-muted">Boundary</dt>
                  <dd className="text-ink">{c.boundary ? c.boundary.approach : <span className="text-ink-muted">Not stated</span>}</dd>
                  <dt className="text-ink-muted">Documents</dt>
                  <dd className="tnum text-ink">{c.documents}</dd>
                </dl>
              </div>
            ))}
          </div>

          <ol className="mt-8 space-y-4">
            {data.rows.map((row) => {
              const max = Math.max(...row.cells.map((c) => c.normalized_value ?? 0), 0) || 1;
              const series = data.series[row.metric_key] ?? {};
              return (
                <li key={row.metric_key} className="rounded-sm border border-rule bg-surface">
                  <div className="flex flex-col gap-1 border-b border-rule px-4 py-3 sm:flex-row sm:items-baseline sm:justify-between">
                    <div>
                      <h3 className="text-ui font-semibold text-ink">
                        {row.label} <span className="font-normal text-ink-muted">· {unit(row.unit)}</span>
                      </h3>
                      <p className="text-ui-sm text-ink-muted">{row.question}</p>
                    </div>
                    <p className="text-ui-sm">
                      <span className={row.comparable ? "text-forest" : "text-brass-deep"}>{row.comparability}</span>
                      <span className="ml-2 tnum text-ink-muted">Disclosed {row.coverage}</span>
                    </p>
                  </div>
                  <ul className="divide-y divide-rule">
                    {row.cells.map((cell) => {
                      const focal = cell.company_id === companyId;
                      const disclosed = cell.status === "disclosed" && cell.normalized_value !== null && cell.normalized_value !== undefined;
                      const width = disclosed ? Math.max(1.5, ((cell.normalized_value ?? 0) / max) * 100) : 100;
                      return (
                        <li key={cell.company_id} className="grid gap-x-4 gap-y-1.5 px-4 py-2.5 md:grid-cols-[11rem_minmax(0,1fr)_14rem]">
                          <span className={cx("text-ui-sm", focal ? "font-medium text-ink" : "text-ink-muted")}>{names[cell.company_id]}</span>
                          <div className="min-w-0">
                            <div className="flex items-center gap-3">
                              <div className="relative h-3 flex-1">
                                {disclosed ? (
                                  <div className={cx("h-full rounded-[1px]", focal ? "bg-ink" : "bg-slate")} style={{ width: `${width}%` }} />
                                ) : (
                                  <div className="h-full w-full rounded-[1px] border border-dashed border-rule-strong" />
                                )}
                              </div>
                              <span className="tnum w-36 shrink-0 text-right text-ui-sm text-ink">
                                {disclosed ? (
                                  <>
                                    {num(cell.normalized_value)} <span className="text-ink-muted">{unit(cell.normalized_unit)}</span>
                                  </>
                                ) : (
                                  <span className="text-ink-muted">Not disclosed</span>
                                )}
                              </span>
                            </div>
                            {cell.notes.length ? (
                              <ul className="mt-1.5 flex flex-wrap gap-x-3 gap-y-1">
                                {cell.notes.filter((n) => n.kind !== "missing").map((n, i) => (
                                  <li key={i} className="text-meta text-ink-muted">
                                    <span className="mr-1 font-medium text-ink">{NOTE_LABEL[n.kind] ?? n.kind}</span>
                                    {unit(n.text)}
                                  </li>
                                ))}
                              </ul>
                            ) : null}
                          </div>
                          <div className="flex flex-col gap-1 md:items-end">
                            {disclosed && cell.source ? (
                              <Link href={sourceHref(cell)} className="text-meta text-ink underline decoration-rule-strong underline-offset-2 hover:decoration-ink">
                                {cell.source} · {cell.period_label}
                              </Link>
                            ) : null}
                            {series[cell.company_id]?.length ? <Sparkline points={series[cell.company_id]} /> : null}
                          </div>
                        </li>
                      );
                    })}
                  </ul>
                </li>
              );
            })}
          </ol>
        </>
      )}
      <PeerEditor key={String(editing)} open={editing} onClose={() => setEditing(false)} companyId={companyId} current={company.peer_ids ?? []} />
    </div>
  );
}
