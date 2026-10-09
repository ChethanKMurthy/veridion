"use client";

import Link from "next/link";
import { Fragment, useMemo, useRef, useState, type ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { ErrorState, Notice, Skeleton } from "@/components/ui/feedback";
import { Field, Segmented, Select, Textarea } from "@/components/ui/field";
import { ArrowUpRight, Close, Document } from "@/components/ui/icons";
import { CompletenessBar, ConfidenceDots } from "@/components/ui/meter";
import { IdTag, useToast } from "@/components/ui/overlay";
import { StatusGlyph, StatusLabel } from "@/components/ui/status";
import { useApi, useClient, useHref, useInvalidate } from "@/lib/api/context";
import type { Action, ElementResult, EvidenceLink, FindingTrail, Passage, Status } from "@/lib/api/types";
import { ACTION_STATUS, STATUS, cx, date, dateTime, num, pct, unit } from "@/lib/format";
import { PageExcerpt, type Highlight } from "./page-view";

const EV_ID = /ev_[0-9a-f]{20}/g;

function TrailStep({
  n,
  title,
  id,
  children,
  last = false,
  meta,
}: {
  n?: number;
  title: string;
  id: string;
  children: ReactNode;
  last?: boolean;
  meta?: ReactNode;
}) {
  return (
    <li id={id} className="relative grid grid-cols-[1.75rem_1fr] gap-x-3 scroll-mt-28">
      <div className="relative flex justify-center">
        <span
          className={cx(
            "relative z-[1] mt-0.5 inline-flex size-6 items-center justify-center rounded-full border text-[0.7rem] tnum",
            n ? "border-ink bg-surface text-ink" : "border-rule-strong bg-surface text-ink-muted",
          )}
          aria-hidden="true"
        >
          {n ?? "·"}
        </span>
        {!last ? <span className="absolute bottom-0 top-7 w-px bg-rule-strong" aria-hidden="true" /> : null}
      </div>
      <div className="min-w-0 pb-8">
        <div className="flex items-baseline justify-between gap-3">
          <h3 className="text-ui font-semibold text-ink">{title}</h3>
          {meta ? <div className="text-meta text-ink-muted">{meta}</div> : null}
        </div>
        <div className="mt-2.5">{children}</div>
      </div>
    </li>
  );
}

function ElementRow({ e, active, onClick }: { e: ElementResult; active: boolean; onClick: () => void }) {
  const icon =
    e.status === "satisfied" ? (
      <StatusGlyph status={e.weak ? "partially_supported" : "supported"} size={11} />
    ) : e.status === "missing" ? (
      <StatusGlyph status="not_found" size={11} />
    ) : (
      <span className="inline-block h-px w-2.5 bg-slate" aria-hidden="true" />
    );
  const label = e.status === "satisfied" ? (e.weak ? "Weak evidence" : "Evidenced") : e.status === "missing" ? "Missing" : "Not applicable";
  return (
    <li>
      <button
        type="button"
        onClick={onClick}
        disabled={!e.passage_ids.length}
        className={cx(
          "grid w-full grid-cols-[1rem_1fr_auto] items-start gap-x-2.5 rounded-sm px-2 py-1.5 text-left transition-colors duration-150",
          active ? "bg-brass-tint" : e.passage_ids.length ? "hover:bg-shade" : "cursor-default",
        )}
        aria-pressed={active}
      >
        <span className="mt-1 flex justify-center" title={label}>
          {icon}
        </span>
        <span className="min-w-0">
          <span className={cx("block text-ui-sm", e.status === "not_applicable" ? "text-ink-muted line-through decoration-rule-strong" : "text-ink")}>
            {e.label}
          </span>
          <span className="mt-0.5 block text-meta leading-snug text-ink-muted">
            <span className="sr-only">{label}. </span>
            {e.note}
            {e.source === "model" ? <span className="ml-1 text-brass-deep">· adjusted by model</span> : null}
          </span>
        </span>
        <span className="tnum text-meta text-slate" title="Weight in the completeness score">
          ×{e.weight}
        </span>
      </button>
    </li>
  );
}

function PassageText({ passage }: { passage: Passage }) {
  if (passage.kind === "table_row" && passage.cells?.label) {
    const headers = passage.cells.headers ?? [];
    return (
      <div className="text-ui-sm">
        {passage.cells.caption ? <p className="text-meta text-ink-muted">{passage.cells.caption}</p> : null}
        <p className="mt-0.5 font-medium text-ink">{passage.cells.label}</p>
        <dl className="mt-1 flex flex-wrap gap-x-4 gap-y-0.5">
          {(passage.cells.values ?? []).map((v, i) =>
            v ? (
              <div key={i} className="flex gap-1.5">
                <dt className="text-ink-muted">{headers[i] || "Value"}</dt>
                <dd className="tnum text-ink">{v}</dd>
              </div>
            ) : null,
          )}
        </dl>
      </div>
    );
  }
  return <p className="text-ui-sm leading-relaxed text-ink">{passage.text}</p>;
}

function EvidenceItem({
  link,
  index,
  active,
  onSelect,
  docHref,
}: {
  link: EvidenceLink;
  index: number;
  active: boolean;
  onSelect: () => void;
  docHref: string;
}) {
  const p = link.passage;
  const roleLabel = { supporting: "Supporting", conflicting: "Conflicting", related: "Related" }[link.role];
  return (
    <li>
      <div
        className={cx(
          "rounded-sm border px-3 py-2.5 transition-colors duration-150",
          active ? "border-ink bg-surface" : "border-rule bg-surface hover:border-rule-strong",
        )}
      >
        <button type="button" onClick={onSelect} className="block w-full text-left" aria-pressed={active}>
          <span className="flex items-center justify-between gap-2 text-meta">
            <span className="flex min-w-0 items-center gap-1.5 text-ink-muted">
              <span className="tnum inline-flex size-4 items-center justify-center rounded-[2px] bg-shade text-[0.65rem] text-ink">{index}</span>
              <span className={cx(link.role === "conflicting" ? "text-oxide" : link.role === "related" ? "text-ink-muted" : "text-forest")}>
                {roleLabel}
              </span>
              <span aria-hidden="true">·</span>
              <span className="truncate">
                {p.document?.short_name ?? "Document"}, p.{p.page}
              </span>
              {p.extraction_method === "ocr" ? <span className="text-brass-deep">· OCR {p.confidence.toFixed(2)}</span> : null}
            </span>
          </span>
          {p.section ? <span className="mt-1 block truncate text-meta text-slate">{p.section}</span> : null}
          <span className="mt-1.5 block">
            <PassageText passage={p} />
          </span>
        </button>
        <div className="mt-2 flex flex-wrap items-center justify-between gap-2">
          <span className="flex flex-wrap gap-1">
            {link.element_keys.map((k) => (
              <span key={k} className="rounded-[2px] bg-shade px-1.5 py-0.5 font-mono text-[0.65rem] text-ink-muted">
                {k}
              </span>
            ))}
          </span>
          <Link href={docHref} className="inline-flex items-center gap-1 text-meta font-medium text-ink hover:underline">
            Open source <ArrowUpRight size={12} />
          </Link>
        </div>
      </div>
    </li>
  );
}

function RationaleText({ text, order, onCite }: { text: string; order: Map<string, number>; onCite: (id: string) => void }) {
  const parts = text.split(/(\[?ev_[0-9a-f]{20}\]?)/g);
  return (
    <p className="text-ui leading-relaxed text-ink">
      {parts.map((part, i) => {
        const id = part.match(EV_ID)?.[0];
        if (!id) return <Fragment key={i}>{part.replace(/\(\s*,?\s*\)|\s+,/g, "")}</Fragment>;
        const n = order.get(id);
        return (
          <button
            key={i}
            type="button"
            onClick={() => onCite(id)}
            className="mx-0.5 inline-flex h-4 min-w-4 items-center justify-center rounded-[2px] bg-shade px-1 align-baseline text-[0.65rem] font-medium text-ink tnum hover:bg-brass-tint"
            title={`Show cited passage ${id}`}
          >
            {n ?? "↗"}
          </button>
        );
      })}
    </p>
  );
}

function ActionRow({ action }: { action: Action }) {
  const client = useClient();
  const invalidate = useInvalidate();
  const toast = useToast();
  const [saving, setSaving] = useState(false);
  const [owner, setOwner] = useState(action.owner ?? "");
  const p = action.priority_components;

  const save = async (patch: Partial<Action>) => {
    setSaving(true);
    try {
      await client.send("PATCH", `/actions/${action.id}`, patch);
      await invalidate("/findings/", `/companies/${action.company_id}/actions`, "/dashboard");
      toast(client.mode === "demo" ? "Updated for this demo session" : "Action updated", "success");
    } catch (err) {
      toast(err instanceof Error ? err.message : "Could not update the action", "danger");
    } finally {
      setSaving(false);
    }
  };

  return (
    <li className="rounded-sm border border-rule bg-surface px-3 py-3">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-ui-sm font-medium text-ink">{action.title}</p>
          {action.detail ? <p className="mt-1 text-meta leading-relaxed text-ink-muted">{action.detail}</p> : null}
        </div>
        <span className="tnum shrink-0 text-ui-sm font-medium text-ink" title={p.explanation}>
          P {num(action.priority_score)}
        </span>
      </div>
      <p className="mt-2 text-meta text-ink-muted tnum">
        Importance {p.I ?? "—"} × gap {p.G ?? "—"} × urgency {p.U ?? "—"} · {action.effort} effort
      </p>
      {action.gap_closed_run_id ? (
        <Notice tone="success" className="mt-2 py-2 text-ui-sm">
          A later run no longer shows this gap. Confirm and mark it done.
        </Notice>
      ) : null}
      <div className="mt-3 grid grid-cols-[1fr_auto] gap-2">
        <label className="sr-only" htmlFor={`owner-${action.id}`}>
          Owner
        </label>
        <input
          id={`owner-${action.id}`}
          value={owner}
          onChange={(e) => setOwner(e.target.value)}
          onBlur={() => owner !== (action.owner ?? "") && save({ owner: owner || null })}
          placeholder="Assign an owner"
          className="h-8 min-w-0 rounded-sm border border-rule-strong bg-surface px-2.5 text-ui-sm placeholder:text-ink-muted/80 focus:border-brass-deep focus:outline-none"
        />
        <Select
          aria-label="Action status"
          value={action.status}
          disabled={saving}
          onChange={(e) => save({ status: e.target.value as Action["status"] })}
          className="h-8 w-36 text-ui-sm"
        >
          {Object.entries(ACTION_STATUS).map(([k, v]) => (
            <option key={k} value={k}>
              {v}
            </option>
          ))}
        </Select>
      </div>
    </li>
  );
}

function ReviewPanel({ trail }: { trail: FindingTrail }) {
  const client = useClient();
  const invalidate = useInvalidate();
  const toast = useToast();
  const [decision, setDecision] = useState<"accept" | "override" | "comment">("accept");
  const [status, setStatus] = useState<Status>(trail.finding.status === "supported" ? "partially_supported" : "supported");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      await client.send("POST", `/findings/${trail.finding.id}/reviews`, {
        decision,
        new_status: decision === "override" ? status : null,
        note,
      });
      setNote("");
      await invalidate(`/findings/${trail.finding.id}`, `/runs/${trail.finding.run_id}/findings`, "/dashboard");
      toast(client.mode === "demo" ? "Review recorded for this demo session" : "Review recorded", "success");
    } catch (err) {
      setError(err instanceof Error ? err.message : "The review could not be saved.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-4">
      {trail.reviews.length ? (
        <ol className="space-y-2">
          {trail.reviews.map((r) => (
            <li key={r.id} className="rounded-sm bg-shade px-3 py-2 text-ui-sm">
              <p className="text-ink">
                <span className="font-medium">{r.reviewer_name ?? "Reviewer"}</span>{" "}
                {r.decision === "accept" ? "accepted the finding" : r.decision === "override" ? (
                  <>
                    overrode the status to <StatusLabel status={r.new_status ?? r.previous_status} short />
                  </>
                ) : (
                  "commented"
                )}
                <span className="ml-1.5 text-meta text-ink-muted">{dateTime(r.created_at)}</span>
              </p>
              {r.note ? <p className="mt-1 text-ink-muted">{r.note}</p> : null}
            </li>
          ))}
        </ol>
      ) : (
        <p className="text-ui-sm text-ink-muted">No review yet. The original assessment is always preserved; reviews are recorded beside it.</p>
      )}
      <div className="space-y-3 rounded-sm border border-rule bg-surface p-3">
        <Segmented
          label="Review decision"
          value={decision}
          onChange={setDecision}
          options={[
            { value: "accept", label: "Accept" },
            { value: "override", label: "Override" },
            { value: "comment", label: "Comment" },
          ]}
        />
        {decision === "override" ? (
          <Field label="Corrected status">
            {(p) => (
              <Select {...p} value={status} onChange={(e) => setStatus(e.target.value as Status)}>
                {(Object.keys(STATUS) as Status[]).map((s) => (
                  <option key={s} value={s}>
                    {STATUS[s].label}
                  </option>
                ))}
              </Select>
            )}
          </Field>
        ) : null}
        <Field
          label={decision === "accept" ? "Note" : "Reason"}
          optional={decision === "accept"}
          hint={decision === "override" ? "Explain the correction so it can be audited later." : undefined}
          error={error}
        >
          {(p) => <Textarea {...p} rows={3} value={note} onChange={(e) => setNote(e.target.value)} className="min-h-20" />}
        </Field>
        <div className="flex justify-end">
          <Button
            variant="primary"
            size="sm"
            loading={busy}
            onClick={submit}
            disabled={(decision !== "accept" && !note.trim()) || busy}
          >
            {decision === "accept" ? "Accept finding" : decision === "override" ? "Record override" : "Add comment"}
          </Button>
        </div>
      </div>
    </div>
  );
}

export function FindingInspector({
  findingId,
  companyId,
  onClose,
}: {
  findingId: string;
  companyId: string;
  onClose?: () => void;
}) {
  const { data: trail, error, isLoading, mutate } = useApi<FindingTrail>(`/findings/${findingId}`);
  const href = useHref();
  const [activeEvidence, setActiveEvidence] = useState<string | null>(null);
  const [activeElement, setActiveElement] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const evidence = useMemo(() => trail?.evidence ?? [], [trail]);
  const order = useMemo(() => new Map(evidence.map((e, i) => [e.passage.id, i + 1])), [evidence]);
  const selected =
    evidence.find((e) => e.passage.id === activeEvidence) ??
    (activeElement ? evidence.find((e) => e.element_keys.includes(activeElement)) : undefined) ??
    evidence[0];

  if (error) return <div className="p-5"><ErrorState error={error} retry={() => mutate()} /></div>;
  if (isLoading || !trail) {
    return (
      <div className="space-y-4 p-5" aria-busy="true">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-6 w-3/4" />
        <Skeleton className="h-40" />
        <Skeleton className="h-64" />
      </div>
    );
  }

  const f = trail.finding;
  const req = trail.requirement;
  const visible = activeElement ? evidence.filter((e) => e.element_keys.includes(activeElement)) : evidence;
  const pageEvidence = selected ? evidence.filter((e) => e.passage.document_id === selected.passage.document_id && e.passage.page === selected.passage.page) : [];
  const highlights: Highlight[] = pageEvidence.map((e) => ({
    id: e.passage.id,
    bbox: e.passage.bbox,
    role: e.role,
    label: `${e.role}: ${e.passage.text.slice(0, 80)}`,
  }));
  const pageSize = selected?.passage.document?.page_sizes?.[selected.passage.page - 1];
  const docHref = (p: Passage) => href(`/companies/${companyId}/documents/${p.document_id}?page=${p.page}&passage=${p.id}`);
  const llm = f.llm_output;
  const gaps = f.element_results.filter((e) => e.status === "missing");
  const run = trail.run;

  const cite = (id: string) => {
    setActiveElement(null);
    setActiveEvidence(id);
    document.getElementById("trail-evidence")?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const jumps: { id: string; label: string; present: boolean }[] = [
    { id: "trail-requirement", label: "Requirement", present: true },
    { id: "trail-evidence", label: "Evidence", present: evidence.length > 0 },
    { id: "trail-rationale", label: "Rationale", present: true },
    { id: "trail-gap", label: "Gap", present: gaps.length > 0 || f.conflicts.length > 0 },
    { id: "trail-action", label: "Action", present: trail.actions.length > 0 },
  ];

  return (
    <div className="flex h-full min-h-0 flex-col bg-canvas">
      <header className="@container border-b border-rule bg-surface px-5 pb-3 pt-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="text-meta text-ink-muted">
              <span className="font-mono">{req.display_code}</span> · {req.topic}
            </p>
            <h2 className="mt-1 text-[1.05rem] font-semibold leading-snug text-ink">{req.title}</h2>
          </div>
          {onClose ? (
            <button
              type="button"
              onClick={onClose}
              aria-label="Close inspector"
              className="-mr-1.5 inline-flex size-8 shrink-0 items-center justify-center rounded-sm text-ink-muted hover:bg-shade hover:text-ink"
            >
              <Close />
            </button>
          ) : null}
        </div>
        <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2">
          <StatusLabel status={f.status} pill />
          <CompletenessBar elements={f.element_results} value={f.completeness} />
          <ConfidenceDots value={f.confidence} />
        </div>
        {f.review.state !== "unreviewed" ? (
          <p className="mt-2 text-meta text-ink-muted">
            Reviewed: {f.review.state === "overridden" ? (
              <>status overridden to <StatusLabel status={f.review.effective_status} short /></>
            ) : (
              "accepted"
            )}{" "}
            by {f.review.latest?.reviewer_name ?? "a reviewer"}
          </p>
        ) : null}
        {/* Connectors only where the five steps fit on one line; narrower panels wrap without them. */}
        <nav aria-label="Jump to step" className="mt-3 flex flex-wrap items-center gap-1 @[24rem]:flex-nowrap">
          {jumps.map((j, i) => (
            <Fragment key={j.id}>
              {i > 0 ? <span className="hidden h-px min-w-1.5 flex-1 bg-rule-strong @[24rem]:block" aria-hidden="true" /> : null}
              <button
                type="button"
                onClick={() => document.getElementById(j.id)?.scrollIntoView({ behavior: "smooth", block: "start" })}
                className={cx(
                  "inline-flex shrink-0 items-center gap-1.5 rounded-sm px-1 py-1 text-meta transition-colors hover:bg-shade",
                  j.present ? "text-ink" : "text-ink-muted",
                )}
              >
                <span className={cx("size-1.5 rounded-full", j.present ? "bg-ink" : "border border-slate")} aria-hidden="true" />
                {j.label}
              </button>
            </Fragment>
          ))}
        </nav>
      </header>

      <div ref={scrollRef} className="min-h-0 flex-1 overflow-y-auto px-5 pt-5 scrollbar-quiet">
        <ol>
          <TrailStep n={1} id="trail-requirement" title="Requirement" meta={<span title="Importance in prioritisation">Importance {req.importance}/3</span>}>
            <p className="text-ui-sm leading-relaxed text-ink-muted">{req.summary}</p>
            <p className="mt-2 text-meta text-ink-muted">
              {req.source_url ? (
                <a href={req.source_url} target="_blank" rel="noreferrer" className="underline decoration-rule-strong underline-offset-2 hover:text-ink">
                  {req.source_reference}
                </a>
              ) : (
                req.source_reference
              )}
              {req.applicability ? <> · {req.applicability}</> : null}
            </p>
            <ul className="mt-3 space-y-0.5" aria-label="Requirement elements">
              {f.element_results.map((e) => (
                <ElementRow
                  key={e.key}
                  e={e}
                  active={activeElement === e.key}
                  onClick={() => {
                    setActiveElement((cur) => (cur === e.key ? null : e.key));
                    setActiveEvidence(e.passage_ids[0] ?? null);
                  }}
                />
              ))}
            </ul>
          </TrailStep>

          <TrailStep
            n={2}
            id="trail-evidence"
            title="Evidence"
            meta={activeElement ? (
              <button type="button" className="underline underline-offset-2" onClick={() => setActiveElement(null)}>
                Showing “{activeElement}” · show all
              </button>
            ) : (
              `${evidence.length} passage${evidence.length === 1 ? "" : "s"}`
            )}
          >
            {evidence.length ? (
              <>
                {selected ? (
                  <div className="mb-3">
                    <PageExcerpt
                      documentId={selected.passage.document_id}
                      page={selected.passage.page}
                      pageSize={pageSize}
                      highlights={highlights}
                      activeId={selected.passage.id}
                      onSelect={(id) => setActiveEvidence(id)}
                      alt={`${selected.passage.document?.short_name ?? "Document"}, page ${selected.passage.page}, with the cited passage highlighted`}
                    />
                    <p className="mt-1.5 flex items-center justify-between text-meta text-ink-muted">
                      <span className="inline-flex items-center gap-1.5">
                        <Document size={12} /> {selected.passage.document?.title}, page {selected.passage.page}
                      </span>
                      <Link href={docHref(selected.passage)} className="font-medium text-ink hover:underline">
                        Open document
                      </Link>
                    </p>
                  </div>
                ) : null}
                <ul className="space-y-2">
                  {visible.map((link) => (
                    <EvidenceItem
                      key={`${link.passage.id}-${link.role}`}
                      link={link}
                      index={order.get(link.passage.id) ?? 0}
                      active={selected?.passage.id === link.passage.id}
                      onSelect={() => setActiveEvidence(link.passage.id)}
                      docHref={docHref(link.passage)}
                    />
                  ))}
                </ul>
              </>
            ) : (
              <p className="text-ui-sm text-ink-muted">
                No passage in the documents assessed establishes this requirement. Upload further documents, or record a
                review if the evidence exists elsewhere.
              </p>
            )}
          </TrailStep>

          <TrailStep
            n={3}
            id="trail-rationale"
            title="Assessment rationale"
            meta={f.method === "hybrid" ? `Rules + model${run?.llm_model ? ` · ${run.llm_model}` : ""}` : "Deterministic rules"}
          >
            <RationaleText text={f.rationale} order={order} onCite={cite} />
            <dl className="mt-3 grid grid-cols-2 gap-x-4 gap-y-1.5 text-meta">
              <dt className="text-ink-muted">Completeness</dt>
              <dd className="tnum text-ink">{pct(f.completeness)} of weighted elements</dd>
              <dt className="text-ink-muted">Citations</dt>
              <dd className="text-ink">
                {f.citation_check?.cited?.length ?? 0} validated
                {f.citation_check?.invalid?.length ? <span className="text-oxide"> · {f.citation_check.invalid.length} discarded</span> : null}
              </dd>
              {f.method === "hybrid" ? (
                <>
                  <dt className="text-ink-muted">Rules · model</dt>
                  <dd className="flex flex-wrap items-center gap-1.5">
                    {f.rules_status ? <StatusLabel status={f.rules_status} short /> : "—"}
                    <span className="text-ink-muted">·</span>
                    {f.llm_status ? <StatusLabel status={f.llm_status} short /> : "—"}
                  </dd>
                </>
              ) : null}
            </dl>
            {llm?.overrides?.length ? (
              <div className="mt-3 rounded-sm bg-shade px-3 py-2.5">
                <p className="text-meta font-medium text-ink">Model adjustments to the rule checks</p>
                <ul className="mt-1.5 space-y-1">
                  {llm.overrides.map((o, i) => (
                    <li key={i} className="text-meta leading-snug text-ink-muted">
                      <span className="font-mono text-ink">{o.element ?? "status"}</span>: {o.from.replace("_", " ")} →{" "}
                      {o.to.replace("_", " ")}. {o.reason}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            {f.review_reasons.length ? (
              <Notice tone="warning" title="Why a reviewer should look" className="mt-3">
                <ul className="list-disc space-y-1 pl-4">
                  {f.review_reasons.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </Notice>
            ) : null}
            {f.method === "hybrid" && f.rules_rationale && f.rules_rationale !== f.rationale ? (
              <details className="mt-3 text-meta">
                <summary className="text-ink-muted hover:text-ink">Deterministic rule summary</summary>
                <p className="mt-1.5 leading-relaxed text-ink-muted">{f.rules_rationale}</p>
              </details>
            ) : null}
          </TrailStep>

          <TrailStep n={4} id="trail-gap" title="Gap">
            {f.conflicts.length ? (
              <div className="space-y-2">
                {f.conflicts.map((c) => (
                  <div key={c.metric_key} className="rounded-sm border border-oxide/30 bg-oxide-tint px-3 py-3">
                    <p className="text-ui-sm font-medium text-ink">
                      {c.label} · {c.period}
                    </p>
                    <div className="mt-2 grid grid-cols-[1fr_auto_1fr] items-center gap-2 text-ui-sm">
                      {[c.low, c.high].map((v, i) => (
                        <Fragment key={v.metric_id}>
                          {i === 1 ? <span className="text-meta text-oxide">vs</span> : null}
                          <button type="button" onClick={() => cite(v.passage_id)} className="rounded-sm bg-surface px-2.5 py-2 text-left hover:shadow-[inset_0_0_0_1px_var(--color-oxide)]">
                            <span className="tnum block font-medium text-ink">
                              {num(v.value)} {unit(v.unit)}
                            </span>
                            {v.unit !== v.normalized_unit ? (
                              <span className="tnum block text-meta text-ink-muted">
                                = {num(v.normalized_value)} {unit(v.normalized_unit)}
                              </span>
                            ) : null}
                            <span className="mt-0.5 block text-meta text-ink-muted">{v.source}</span>
                          </button>
                        </Fragment>
                      ))}
                    </div>
                    <p className="mt-2 text-meta text-ink-muted">
                      {pct(c.relative_difference, 1)} apart after converting to {unit(c.unit)}. Tolerance is 1%.
                    </p>
                  </div>
                ))}
              </div>
            ) : null}
            {gaps.length ? (
              <ul className={cx("space-y-1", f.conflicts.length > 0 && "mt-3")}>
                {gaps.map((g) => (
                  <li key={g.key} className="flex items-start gap-2 text-ui-sm">
                    <StatusGlyph status="not_found" size={11} className="mt-1" />
                    <span>
                      <span className="text-ink">{g.label}</span>
                      <span className="block text-meta text-ink-muted">{g.note}</span>
                    </span>
                  </li>
                ))}
              </ul>
            ) : null}
            {!gaps.length && !f.conflicts.length ? (
              <p className="text-ui-sm text-ink-muted">No open gap for this requirement in this run.</p>
            ) : (
              <p className="mt-3 text-meta text-ink-muted">
                Absence of evidence in the documents provided is not evidence of non-compliance.
              </p>
            )}
          </TrailStep>

          <TrailStep n={5} id="trail-action" title="Recommended action" meta={trail.actions.length ? `${trail.actions.length} linked` : undefined}>
            {trail.actions.length ? (
              <ul className="space-y-2">
                {trail.actions.map((a) => (
                  <ActionRow key={a.id} action={a} />
                ))}
              </ul>
            ) : (
              <p className="text-ui-sm text-ink-muted">Nothing to remediate for this requirement.</p>
            )}
          </TrailStep>

          <TrailStep id="trail-review" title="Review" last>
            <ReviewPanel trail={trail} />
            <dl className="mt-6 grid grid-cols-[auto_1fr] gap-x-4 gap-y-1.5 border-t border-rule pt-4 text-meta">
              <dt className="text-ink-muted">Finding</dt>
              <dd className="min-w-0"><IdTag value={f.id} label="finding id" /></dd>
              <dt className="text-ink-muted">Run</dt>
              <dd className="min-w-0"><IdTag value={f.run_id} label="run id" /></dd>
              <dt className="text-ink-muted">Catalogue</dt>
              <dd className="font-mono text-[0.7rem] text-ink-muted">{req.set_id}</dd>
              <dt className="text-ink-muted">Requirement hash</dt>
              <dd className="truncate font-mono text-[0.7rem] text-ink-muted" title={req.content_hash}>{req.content_hash.slice(0, 16)}</dd>
              {run ? (
                <>
                  <dt className="text-ink-muted">Versions</dt>
                  <dd className="font-mono text-[0.7rem] text-ink-muted">
                    {[run.pipeline_version, run.rules_version, run.prompt_version].filter(Boolean).join(" · ")}
                  </dd>
                  <dt className="text-ink-muted">Assessed</dt>
                  <dd className="text-ink-muted">{date(run.finished_at)}</dd>
                </>
              ) : null}
            </dl>
            {trail.history.length > 1 ? (
              <div className="mt-4">
                <p className="text-meta font-medium text-ink">History of this requirement</p>
                <ol className="mt-1.5 space-y-1">
                  {trail.history.map((h) => (
                    <li key={h.finding_id} className="flex items-center justify-between gap-2 text-meta text-ink-muted">
                      <span className="font-mono text-[0.7rem]">{h.requirement_set_id.split("@")[1]}</span>
                      <StatusLabel status={h.status} short />
                      <span className="tnum">{pct(h.completeness)}</span>
                      <span>{date(h.created_at)}</span>
                    </li>
                  ))}
                </ol>
              </div>
            ) : null}
          </TrailStep>
        </ol>
      </div>
    </div>
  );
}
