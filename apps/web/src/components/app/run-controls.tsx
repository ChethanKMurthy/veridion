"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Notice } from "@/components/ui/feedback";
import { Field, Input, Segmented, Select } from "@/components/ui/field";
import { Dialog } from "@/components/ui/overlay";
import { ApiError } from "@/lib/api/client";
import { useApi, useClient, useInvalidate } from "@/lib/api/context";
import type { OrgInfo, RequirementSet, Run } from "@/lib/api/types";
import { cx, date } from "@/lib/format";

const SET_STATUS: Record<RequirementSet["status"], string> = {
  in_force: "In force",
  upcoming: "Upcoming",
  withdrawn: "Withdrawn",
};

export function NewRunDialog({
  open,
  onClose,
  companyId,
  onCreated,
}: {
  open: boolean;
  onClose: () => void;
  companyId: string;
  onCreated: (run: Run) => void;
}) {
  const client = useClient();
  const invalidate = useInvalidate();
  const { data: sets } = useApi<RequirementSet[]>(open ? "/requirement-sets" : null);
  const { data: org } = useApi<OrgInfo>(open && client.mode === "live" ? "/org" : null);
  const [setId, setSetId] = useState("");
  const [period, setPeriod] = useState("FY2025");
  const [mode, setMode] = useState<"rules" | "hybrid">("rules");
  const [deadline, setDeadline] = useState("");
  const [label, setLabel] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<ApiError | Error | null>(null);

  const ordered = useMemo(
    () =>
      [...(sets ?? [])].sort((a, b) => {
        const rank = { in_force: 0, upcoming: 1, withdrawn: 2 } as const;
        return rank[a.status] - rank[b.status] || b.version.localeCompare(a.version, undefined, { numeric: true });
      }),
    [sets],
  );
  const selectedSetId = setId || ordered[0]?.id || "";
  const close = () => {
    setError(null);
    onClose();
  };

  const chosen = ordered.find((s) => s.id === selectedSetId);
  const llmAvailable = client.mode === "demo" ? true : Boolean(org?.llm_available);

  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      const run = await client.send<Run>("POST", `/companies/${companyId}/runs`, {
        requirement_set_id: selectedSetId,
        mode,
        period_label: period.trim(),
        deadline: deadline || null,
        label: label.trim() || null,
      });
      await invalidate(`/companies/${companyId}`, "/dashboard");
      onCreated(run);
    } catch (err) {
      setError(err as Error);
    } finally {
      setBusy(false);
    }
  };

  const code = (error as ApiError | null)?.code;

  return (
    <Dialog
      open={open}
      onClose={close}
      title="New assessment"
      description="Assess this company's current documents against a versioned requirement catalogue. Earlier runs are kept for comparison."
      footer={
        <>
          <Button variant="ghost" onClick={close}>
            Cancel
          </Button>
          <Button variant="primary" onClick={submit} loading={busy} disabled={!selectedSetId || !period.trim()}>
            Start assessment
          </Button>
        </>
      }
    >
      <div className="space-y-5">
        <Field label="Requirement catalogue">
          {(p) => (
            <Select {...p} value={selectedSetId} onChange={(e) => setSetId(e.target.value)}>
              {ordered.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.title} — v{s.version} ({SET_STATUS[s.status]}
                  {s.review_status === "draft" ? ", draft" : ""})
                </option>
              ))}
            </Select>
          )}
        </Field>
        {chosen ? (
          <div className="-mt-2 text-meta text-ink-muted">
            {chosen.requirement_count} requirements ·{" "}
            {chosen.effective_from ? `effective from ${date(chosen.effective_from)}` : "no effective date"}
            {chosen.effective_to ? ` to ${date(chosen.effective_to)}` : ""}
            {chosen.review_status === "draft" ? (
              <Notice tone="warning" className="mt-2">
                This catalogue is a draft. Its element definitions have not been verified against the official text, so treat
                results as indicative.
              </Notice>
            ) : null}
            {chosen.status === "upcoming" ? (
              <Notice tone="info" className="mt-2">
                Not yet in force. Use it to prepare for early adoption.
              </Notice>
            ) : null}
          </div>
        ) : null}

        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Reporting period" hint="Financial year, e.g. FY2025">
            {(p) => <Input {...p} value={period} onChange={(e) => setPeriod(e.target.value)} />}
          </Field>
          <Field label="Reporting deadline" optional hint="Used to rank actions by urgency">
            {(p) => <Input {...p} type="date" value={deadline} onChange={(e) => setDeadline(e.target.value)} />}
          </Field>
        </div>

        <div>
          <p className="text-ui-sm font-medium text-ink">Method</p>
          <Segmented
            className="mt-1.5"
            label="Assessment method"
            value={mode}
            onChange={setMode}
            options={[
              { value: "rules", label: "Rules only" },
              { value: "hybrid", label: "Rules + model" },
            ]}
          />
          <p className="mt-2 text-meta leading-relaxed text-ink-muted">
            {mode === "rules"
              ? "Deterministic checks: extracted values, units, periods and wording. Fast, free and fully reproducible."
              : "Adds a language model that reviews each requirement against the cited passages. It can only cite passages Veridion found, and it cannot override detected conflicts."}
          </p>
          {mode === "hybrid" && !llmAvailable ? (
            <Notice tone="warning" className="mt-2">
              No model provider is configured on this deployment. Use rules-only mode.
            </Notice>
          ) : null}
        </div>

        <Field label="Label" optional>
          {(p) => (
            <Input {...p} value={label} onChange={(e) => setLabel(e.target.value)} placeholder="e.g. Pre-audit review" maxLength={200} />
          )}
        </Field>

        {error ? (
          <Notice tone={code === "plan_limit" ? "warning" : "danger"} title={code === "demo_read_only" ? "Available with access" : undefined}>
            {error.message}
            {code === "demo_read_only" || code === "plan_limit" ? (
              <>
                {" "}
                <Link href={code === "plan_limit" ? "/pricing" : "/request-access"} className="font-medium text-ink underline underline-offset-2">
                  {code === "plan_limit" ? "Compare plans" : "Request access"}
                </Link>
              </>
            ) : null}
          </Notice>
        ) : null}
      </div>
    </Dialog>
  );
}

export function RunProgress({ run, onDone, className }: { run: Run; onDone?: () => void; className?: string }) {
  const pct = Math.max(4, Math.min(100, run.job?.progress?.pct ?? (run.status === "queued" ? 2 : 10)));
  useEffect(() => {
    if (run.status === "completed" || run.status === "failed") onDone?.();
  }, [run.status, onDone]);
  return (
    <div className={cx("rounded-sm border border-rule bg-surface px-4 py-3", className)} role="status" aria-live="polite">
      <div className="flex items-center justify-between gap-3 text-ui-sm">
        <span className="font-medium text-ink">
          {run.status === "queued" ? "Waiting for a worker" : "Assessment in progress"} · {run.requirement_set_id}
        </span>
        <span className="tnum text-ink-muted">{Math.round(pct)}%</span>
      </div>
      <div className="mt-2 h-1 overflow-hidden rounded-full bg-shade">
        <div className="h-full bg-ink transition-[width] duration-500 ease-[var(--ease-out-quart)]" style={{ width: `${pct}%` }} />
      </div>
      <p className="mt-1.5 text-meta text-ink-muted">{run.job?.progress?.message ?? "Starting…"}</p>
    </div>
  );
}
