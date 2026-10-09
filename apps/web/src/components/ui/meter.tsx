import type { ElementResult } from "@/lib/api/types";
import { cx, pct } from "@/lib/format";

/**
 * Evidence completeness as weighted segments: each element occupies width proportional
 * to its weight; filled when evidenced, hatched when weakly evidenced, empty when missing.
 */
export function CompletenessBar({
  elements,
  value,
  className,
}: {
  elements?: ElementResult[];
  value: number;
  className?: string;
}) {
  const applicable = (elements ?? []).filter((e) => e.status !== "not_applicable");
  const total = applicable.reduce((s, e) => s + e.weight, 0);
  return (
    <div className={cx("flex items-center gap-2.5", className)}>
      <div
        className="flex h-1.5 w-24 shrink-0 gap-px overflow-hidden rounded-[1px] bg-transparent"
        role="meter"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(value * 100)}
        aria-label="Evidence completeness"
      >
        {applicable.length ? (
          applicable.map((e) => (
            <span
              key={e.key}
              title={`${e.label}: ${e.status === "satisfied" ? (e.weak ? "weak evidence" : "evidenced") : "missing"}`}
              style={{ flexGrow: total ? e.weight / total : 1 }}
              className={cx(
                "h-full",
                e.status === "satisfied"
                  ? e.weak
                    ? "bg-[repeating-linear-gradient(135deg,var(--color-ink)_0_2px,transparent_2px_4px)]"
                    : "bg-ink"
                  : "bg-rule-strong",
              )}
            />
          ))
        ) : (
          <>
            <span className="h-full bg-ink" style={{ flexGrow: value }} />
            <span className="h-full bg-rule-strong" style={{ flexGrow: 1 - value }} />
          </>
        )}
      </div>
      <span className="tnum text-ui-sm text-ink-muted">{pct(value)}</span>
    </div>
  );
}

export function ConfidenceDots({ value, className }: { value: number; className?: string }) {
  const level = value >= 0.85 ? 3 : value >= 0.65 ? 2 : 1;
  const label = level === 3 ? "High" : level === 2 ? "Moderate" : "Low";
  return (
    <span className={cx("inline-flex items-center gap-1.5 text-ui-sm text-ink-muted", className)} title={`Confidence ${value.toFixed(2)}`}>
      <span className="inline-flex gap-0.5" aria-hidden="true">
        {[1, 2, 3].map((i) => (
          <span key={i} className={cx("size-1.5 rounded-full", i <= level ? "bg-ink" : "bg-rule-strong")} />
        ))}
      </span>
      {label}
    </span>
  );
}
