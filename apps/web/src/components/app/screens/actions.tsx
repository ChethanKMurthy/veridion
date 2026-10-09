"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { EmptyState, ErrorState, SkeletonRows } from "@/components/ui/feedback";
import { Segmented, Select } from "@/components/ui/field";
import { useToast } from "@/components/ui/overlay";
import { useApi, useClient, useHref, useInvalidate } from "@/lib/api/context";
import type { Action } from "@/lib/api/types";
import { ACTION_STATUS, cx, num } from "@/lib/format";
import { PageHeader } from "../shell";
import { useCompanyId } from "../company-frame";

type View = "open" | "done" | "all";

function ActionLine({ action, titles }: { action: Action; titles: Record<string, string> }) {
  const client = useClient();
  const invalidate = useInvalidate();
  const toast = useToast();
  const href = useHref();
  const [owner, setOwner] = useState(action.owner ?? "");
  const [due, setDue] = useState(action.due_date ?? "");
  const p = action.priority_components;

  const save = async (patch: Partial<Action>) => {
    try {
      await client.send("PATCH", `/actions/${action.id}`, patch);
      await invalidate(`/companies/${action.company_id}/actions`, "/findings/", "/dashboard");
      toast(client.mode === "demo" ? "Updated for this demo session" : "Saved", "success");
    } catch (err) {
      toast(err instanceof Error ? err.message : "Could not save", "danger");
    }
  };

  return (
    <tr className={cx("border-b border-rule align-top last:border-0", (action.status === "done" || action.status === "dismissed") && "text-ink-muted")}>
      <td className="px-4 py-3">
        <span className="tnum block text-[1rem] font-semibold text-ink" title={p.explanation}>
          {num(action.priority_score)}
        </span>
        <span className="tnum mt-0.5 block whitespace-nowrap text-meta text-ink-muted" title="Importance × gap × urgency">
          {p.I ?? "–"} × {p.G ?? "–"} × {p.U ?? "–"}
        </span>
      </td>
      <td className="max-w-[30rem] px-3 py-3">
        <p className="text-ui-sm font-medium text-ink">{action.title}</p>
        {action.detail ? <p className="mt-1 text-meta leading-relaxed text-ink-muted">{action.detail}</p> : null}
        <p className="mt-1.5 text-meta text-ink-muted">
          <Link
            href={href(`/companies/${action.company_id}/evidence?run=${action.run_id}&finding=${action.finding_id}`)}
            className="font-mono text-ink underline decoration-rule-strong underline-offset-2 hover:decoration-ink"
          >
            {action.requirement_code}
          </Link>{" "}
          · gap <span className="font-mono">{action.gap_key}</span> · {action.effort} effort
        </p>
        {action.depends_on.length ? (
          <p className="mt-1 text-meta text-ink-muted">After: {action.depends_on.map((d) => titles[d] ?? d).join("; ")}</p>
        ) : null}
        {action.gap_closed_run_id ? (
          <p className="mt-1.5 text-meta text-forest">The latest run no longer shows this gap — confirm and mark it done.</p>
        ) : null}
      </td>
      <td className="px-3 py-3">
        <label className="sr-only" htmlFor={`o-${action.id}`}>Owner</label>
        <input
          id={`o-${action.id}`}
          value={owner}
          onChange={(e) => setOwner(e.target.value)}
          onBlur={() => owner !== (action.owner ?? "") && save({ owner: owner || null })}
          placeholder="Unassigned"
          className="h-8 w-40 rounded-sm border border-transparent bg-transparent px-2 text-ui-sm hover:border-rule-strong focus:border-brass-deep focus:bg-surface focus:outline-none"
        />
      </td>
      <td className="px-3 py-3">
        <label className="sr-only" htmlFor={`d-${action.id}`}>Due date</label>
        <input
          id={`d-${action.id}`}
          type="date"
          value={due}
          onChange={(e) => setDue(e.target.value)}
          onBlur={() => due !== (action.due_date ?? "") && save({ due_date: due || null })}
          className="h-8 rounded-sm border border-transparent bg-transparent px-2 text-ui-sm hover:border-rule-strong focus:border-brass-deep focus:bg-surface focus:outline-none"
        />
      </td>
      <td className="px-4 py-3">
        <Select aria-label="Status" value={action.status} onChange={(e) => save({ status: e.target.value as Action["status"] })} className="h-8 w-36 text-ui-sm">
          {Object.entries(ACTION_STATUS).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </Select>
      </td>
    </tr>
  );
}

export function ActionsScreen() {
  const companyId = useCompanyId();
  const [view, setView] = useState<View>("open");
  const { data, error, mutate } = useApi<Action[]>(`/companies/${companyId}/actions`);
  const titles = useMemo(() => Object.fromEntries((data ?? []).map((a) => [a.id, a.title])), [data]);
  const rows = (data ?? []).filter((a) =>
    view === "all" ? true : view === "done" ? a.status === "done" || a.status === "dismissed" : !["done", "dismissed"].includes(a.status),
  );
  const counts = {
    open: (data ?? []).filter((a) => !["done", "dismissed"].includes(a.status)).length,
    done: (data ?? []).filter((a) => ["done", "dismissed"].includes(a.status)).length,
    all: data?.length ?? 0,
  };

  return (
    <div className="px-4 py-6 sm:px-6 lg:px-8">
      <PageHeader
        title="Remediation"
        description={
          <>
            Actions are created from the gaps in each assessment and kept across runs. Priority is a working heuristic, not a
            regulatory score: <span className="whitespace-nowrap">P = importance × gap × urgency</span>.
          </>
        }
        actions={
          <Segmented
            label="Show"
            value={view}
            onChange={setView}
            options={[
              { value: "open", label: "Open", count: counts.open },
              { value: "done", label: "Done", count: counts.done },
              { value: "all", label: "All", count: counts.all },
            ]}
          />
        }
      />
      <div className="mt-6 overflow-x-auto rounded-sm border border-rule bg-surface scrollbar-quiet">
        {error ? (
          <div className="p-4"><ErrorState error={error} retry={() => mutate()} /></div>
        ) : !data ? (
          <div className="px-4"><SkeletonRows /></div>
        ) : !rows.length ? (
          <EmptyState className="m-4 border-none" title={view === "open" ? "No open actions" : "Nothing here yet"}>
            {view === "open"
              ? "Every gap from the latest assessment has been resolved or dismissed. New gaps appear here after each run."
              : "Completed and dismissed actions are listed here."}
          </EmptyState>
        ) : (
          <table className="w-full min-w-[900px] text-left">
            <thead>
              <tr className="border-b border-rule text-meta text-ink-muted">
                <th scope="col" className="px-4 py-2.5 font-medium">Priority</th>
                <th scope="col" className="px-3 py-2.5 font-medium">Action</th>
                <th scope="col" className="px-3 py-2.5 font-medium">Owner</th>
                <th scope="col" className="px-3 py-2.5 font-medium">Due</th>
                <th scope="col" className="px-4 py-2.5 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((a) => (
                <ActionLine key={a.id} action={a} titles={titles} />
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
