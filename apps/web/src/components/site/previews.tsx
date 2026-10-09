import Link from "next/link";
import { StatusGlyph, StatusLabel } from "@/components/ui/status";
import { highlights } from "@/lib/highlights";
import { STATUS, STATUS_ORDER, cx, num, pct, unit } from "@/lib/format";
import { PageCrop } from "./page-crop";

/** A faithful, static rendering of the Evidence Explorer using recorded engine output. */
export function ExplorerPreview({ rows = 7, className }: { rows?: number; className?: string }) {
  const h = highlights;
  return (
    <figure className={cx("overflow-hidden rounded-md border border-rule-dark-strong bg-canvas text-ink shadow-[0_30px_80px_-30px_rgba(0,0,0,0.6)]", className)}>
      <div className="flex items-center justify-between gap-3 border-b border-rule bg-surface px-4 py-2.5">
        <div className="min-w-0">
          <p className="truncate text-ui-sm font-medium">{h.company.name} · Evidence</p>
          <p className="truncate font-mono text-[0.68rem] text-ink-muted">
            {h.run.requirement_set_id} · {h.run.mode === "hybrid" ? "rules + model" : "rules"} · {h.run.period_label}
          </p>
        </div>
        <span className="hidden shrink-0 rounded-[2px] bg-brass-tint px-1.5 py-0.5 text-meta text-brass-deep sm:inline">Fictional company</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[560px] text-left text-ui-sm">
          <thead>
            <tr className="border-b border-rule text-meta text-ink-muted">
              <th className="px-4 py-2 font-medium">Requirement</th>
              <th className="px-3 py-2 font-medium">Status</th>
              <th className="px-3 py-2 font-medium">Coverage</th>
              <th className="px-4 py-2 font-medium">Source</th>
            </tr>
          </thead>
          <tbody className="bg-surface">
            {h.findings.slice(0, rows).map((f) => (
              <tr key={f.id} className={cx("border-b border-rule last:border-0", f.status === "conflicting" && "bg-brass-tint")}>
                <td className="px-4 py-2.5">
                  <span className="block font-mono text-[0.68rem] text-ink-muted">{f.display_code}</span>
                  <span className="block text-ink">{f.title}</span>
                </td>
                <td className="px-3 py-2.5"><StatusLabel status={f.status} short /></td>
                <td className="px-3 py-2.5">
                  <span className="flex items-center gap-2">
                    <span className="flex h-1.5 w-16 overflow-hidden rounded-[1px] bg-rule-strong" aria-hidden="true">
                      <span className="h-full bg-ink" style={{ width: `${f.completeness * 100}%` }} />
                    </span>
                    <span className="tnum text-meta text-ink-muted">{pct(f.completeness)}</span>
                  </span>
                </td>
                <td className="px-4 py-2.5 text-meta text-ink-muted">
                  {f.primary_evidence ? `${f.primary_evidence.document}, p.${f.primary_evidence.page}` : "None found"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </figure>
  );
}

/** The conflicting energy figure: both source pages, side by side, as recorded. */
export function ConflictPreview({ dark = false }: { dark?: boolean }) {
  const c = highlights.conflict;
  if (!c?.low || !c.high) return null;
  const k = c.conflict;
  return (
    <div className="space-y-4">
      {[
        { crop: c.low, value: k.low, role: "supporting" as const },
        { crop: c.high, value: k.high, role: "conflicting" as const },
      ].map(({ crop, value, role }) => (
        <figure key={crop.id} className={cx("overflow-hidden rounded-sm border", dark ? "border-rule-dark-strong" : "border-rule")}>
          <PageCrop
            src={crop.src}
            size={crop.size}
            bbox={crop.bbox}
            role={role}
            padY={38}
            padX={24}
            alt={`${crop.title}, page ${crop.page}: ${crop.text}`}
          />
          <figcaption className={cx("flex items-baseline justify-between gap-3 px-3 py-2.5 text-ui-sm", dark ? "bg-graphite text-on-dark" : "bg-surface text-ink")}>
            <span>
              {crop.document}, p.{crop.page}
            </span>
            <span className="tnum">
              {num(value.value)} {unit(value.unit)}
              {value.unit !== value.normalized_unit ? (
                <span className={dark ? "text-on-dark-muted" : "text-ink-muted"}>
                  {" "}= {num(value.normalized_value)} {unit(value.normalized_unit)}
                </span>
              ) : null}
            </span>
          </figcaption>
        </figure>
      ))}
    </div>
  );
}

export function StatusLegend({ className }: { className?: string }) {
  return (
    <dl className={cx("divide-y divide-rule border-y border-rule", className)}>
      {STATUS_ORDER.slice().reverse().map((s) => (
        <div key={s} className="grid gap-1 py-3.5 sm:grid-cols-[13rem_1fr] sm:gap-6">
          <dt className="flex items-center gap-2 text-ui font-medium">
            <StatusGlyph status={s} size={13} />
            <span className={s === "not_found" || s === "human_review" ? "text-ink" : undefined}>{STATUS[s].label}</span>
          </dt>
          <dd className="text-ui text-ink-muted">{STATUS[s].description}</dd>
        </div>
      ))}
    </dl>
  );
}

/** Scope 1 (or another metric) across the fictional peer group, with comparability notes. */
export function BenchmarkPreview({ metric = "ghg_scope1", className }: { metric?: string; className?: string }) {
  const b = highlights.benchmark;
  const row = b.rows.find((r) => r.metric_key === metric);
  if (!row) return null;
  const names = Object.fromEntries(b.companies.map((c) => [c.id, c.name]));
  const focal = b.companies.find((c) => c.is_focal)?.id;
  const max = Math.max(...row.cells.map((c) => c.normalized_value ?? 0)) || 1;
  return (
    <figure className={cx("rounded-sm border border-rule bg-surface", className)}>
      <figcaption className="border-b border-rule px-5 py-4">
        <p className="text-ui font-semibold text-ink">
          {row.label} <span className="font-normal text-ink-muted">· {unit(row.unit)}</span>
        </p>
        <p className="text-ui-sm text-ink-muted">{row.question}</p>
      </figcaption>
      <ul className="divide-y divide-rule">
        {row.cells.map((cell) => {
          const disclosed = cell.status === "disclosed" && cell.normalized_value != null;
          return (
            <li key={cell.company_id} className="px-5 py-3.5">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <span className={cx("text-ui-sm", cell.company_id === focal ? "font-medium text-ink" : "text-ink-muted")}>{names[cell.company_id]}</span>
                <span className="tnum text-ui-sm text-ink">
                  {disclosed ? `${num(cell.normalized_value)} ${unit(cell.normalized_unit)}` : <span className="text-ink-muted">Not disclosed</span>}
                  {disclosed && cell.source ? <span className="ml-2 text-meta text-ink-muted">{cell.source}</span> : null}
                </span>
              </div>
              <div className="mt-2 h-2.5">
                {disclosed ? (
                  <div className={cx("h-full rounded-[1px]", cell.company_id === focal ? "bg-ink" : "bg-slate")} style={{ width: `${((cell.normalized_value ?? 0) / max) * 100}%` }} />
                ) : (
                  <div className="h-full rounded-[1px] border border-dashed border-rule-strong" />
                )}
              </div>
              {cell.notes.filter((n) => n.kind !== "missing").length ? (
                <ul className="mt-2 flex flex-wrap gap-x-4 gap-y-1">
                  {cell.notes.filter((n) => n.kind !== "missing").map((n, i) => (
                    <li key={i} className="text-meta text-ink-muted">{unit(n.text)}</li>
                  ))}
                </ul>
              ) : null}
            </li>
          );
        })}
      </ul>
      <p className="border-t border-rule px-5 py-3 text-meta text-ink-muted">
        {row.comparability}. Fictional companies; values recorded from the Veridion engine.
      </p>
    </figure>
  );
}

export function DemoLink({ path = "", className, children }: { path?: string; className?: string; children: React.ReactNode }) {
  return (
    <Link href={`/demo${path}`} className={className}>
      {children}
    </Link>
  );
}
