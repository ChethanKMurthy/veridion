"use client";

import { useState } from "react";
import { ErrorState, Notice, ScreenSkeleton, Skeleton } from "@/components/ui/feedback";
import { ChevronDown } from "@/components/ui/icons";
import { useApi } from "@/lib/api/context";
import type { RequirementSet } from "@/lib/api/types";
import { cx, date } from "@/lib/format";
import { PageHeader } from "../shell";

const STATUS_TEXT: Record<RequirementSet["status"], string> = { in_force: "In force", upcoming: "Upcoming", withdrawn: "Withdrawn" };
const CHECK_TEXT: Record<string, string> = {
  metric: "Typed value for the period",
  metric_period: "Period stated with the value",
  pattern: "Disclosure wording",
  any_of: "Value or wording",
  conditional: "Applies only when triggered",
};

function SetDetail({ id }: { id: string }) {
  const { data } = useApi<RequirementSet>(`/requirement-sets/${id}`);
  const [open, setOpen] = useState<string | null>(null);
  if (!data) return <Skeleton className="m-4 h-40" />;
  return (
    <div className="border-t border-rule px-4 py-4">
      {data.review_status === "draft" ? (
        <Notice tone="warning" className="mb-4" title="Draft catalogue">
          {data.notes}
        </Notice>
      ) : null}
      {data.effective_rule ? <p className="text-ui-sm leading-relaxed text-ink-muted">{data.effective_rule}</p> : null}
      <ul className="mt-4 divide-y divide-rule rounded-sm border border-rule">
        {data.requirements?.map((r) => {
          const expanded = open === r.id;
          return (
            <li key={r.id}>
              <button
                type="button"
                aria-expanded={expanded}
                onClick={() => setOpen(expanded ? null : r.id)}
                className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left hover:bg-canvas"
              >
                <span>
                  <span className="mr-2 font-mono text-[0.75rem] text-ink-muted">{r.display_code}</span>
                  <span className="text-ui text-ink">{r.title}</span>
                </span>
                <span className="flex shrink-0 items-center gap-3 text-meta text-ink-muted">
                  <span>{r.elements.length} elements</span>
                  <span>importance {r.importance}/3</span>
                  <ChevronDown className={cx("transition-transform", expanded && "rotate-180")} />
                </span>
              </button>
              {expanded ? (
                <div className="bg-canvas px-4 py-4">
                  <p className="text-ui-sm leading-relaxed text-ink">{r.summary}</p>
                  <p className="mt-1.5 text-meta text-ink-muted">
                    {r.source_reference}
                    {r.applicability ? ` · ${r.applicability}` : ""}
                  </p>
                  <table className="mt-3 w-full text-left text-ui-sm">
                    <thead>
                      <tr className="border-b border-rule text-meta text-ink-muted">
                        <th className="py-1.5 pr-3 font-medium">Element</th>
                        <th className="py-1.5 pr-3 text-right font-medium">Weight</th>
                        <th className="py-1.5 pr-3 font-medium">Evidence check</th>
                        <th className="py-1.5 font-medium">Action if missing</th>
                      </tr>
                    </thead>
                    <tbody>
                      {r.elements.map((e) => (
                        <tr key={e.key} className="border-b border-rule align-top last:border-0">
                          <td className="py-2 pr-3 text-ink">{e.label}</td>
                          <td className="tnum py-2 pr-3 text-right text-ink-muted">{e.weight}</td>
                          <td className="py-2 pr-3 text-ink-muted">{CHECK_TEXT[e.check.type] ?? e.check.type}</td>
                          <td className="py-2 text-ink-muted">{e.action.title}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : null}
            </li>
          );
        })}
      </ul>
      {data.changelog.length ? (
        <div className="mt-5">
          <p className="text-meta font-medium text-ink">Changelog</p>
          <ul className="mt-1.5 space-y-2">
            {data.changelog.map((c) => (
              <li key={c.version} className="text-ui-sm">
                <span className="font-mono text-[0.75rem] text-ink">v{c.version}</span>
                <span className="ml-2 text-meta text-ink-muted">{date(c.date)}</span>
                <ul className="mt-0.5 list-disc pl-5 text-ink-muted">
                  {c.changes.map((x) => (
                    <li key={x}>{x}</li>
                  ))}
                </ul>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

export function RequirementsScreen() {
  const { data, error } = useApi<RequirementSet[]>("/requirement-sets");
  const [open, setOpen] = useState<string | null>(null);
  if (error) return <div className="p-6 lg:p-8"><ErrorState error={error} /></div>;
  if (!data) return <ScreenSkeleton />;
  return (
    <div className="px-4 py-6 sm:px-6 lg:px-8">
      <PageHeader
        title="Requirement catalogues"
        description="Versioned, effective-dated requirement sets. A version never changes after it is used; revisions are published as new versions so earlier assessments stay reproducible. Summaries paraphrase the standards — consult the official text."
      />
      <ul className="mt-6 space-y-3">
        {data.map((rs) => (
          <li key={rs.id} className="rounded-sm border border-rule bg-surface">
            <button
              type="button"
              aria-expanded={open === rs.id}
              onClick={() => setOpen(open === rs.id ? null : rs.id)}
              className="flex w-full flex-col gap-2 px-4 py-4 text-left md:flex-row md:items-center md:justify-between"
            >
              <span className="min-w-0">
                <span className="block text-ui font-medium text-ink">{rs.title}</span>
                <span className="block text-ui-sm text-ink-muted">
                  <span className="font-mono text-[0.75rem]">{rs.id}</span> · {rs.requirement_count} requirements ·{" "}
                  {rs.standards.map((s) => s.name).join(", ")}
                </span>
              </span>
              <span className="flex shrink-0 items-center gap-3 text-ui-sm">
                <span className={cx(rs.status === "in_force" ? "text-forest" : rs.status === "upcoming" ? "text-brass-deep" : "text-ink-muted")}>
                  {STATUS_TEXT[rs.status]}
                </span>
                <span className="text-ink-muted">
                  {rs.effective_from ? date(rs.effective_from) : "—"} – {rs.effective_to ? date(rs.effective_to) : "open"}
                </span>
                <span className={cx("rounded-[2px] px-1.5 py-0.5 text-meta", rs.review_status === "draft" ? "bg-brass-tint text-brass-deep" : "bg-forest-tint text-forest")}>
                  {rs.review_status === "draft" ? "Draft" : "Reviewed"}
                </span>
                <ChevronDown className={cx("text-ink-muted transition-transform", open === rs.id && "rotate-180")} />
              </span>
            </button>
            {open === rs.id ? <SetDetail id={rs.id} /> : null}
          </li>
        ))}
      </ul>
    </div>
  );
}
