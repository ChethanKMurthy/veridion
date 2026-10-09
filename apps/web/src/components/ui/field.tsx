"use client";

import { useId, type ComponentProps, type KeyboardEvent, type ReactNode } from "react";
import { cx } from "@/lib/format";

const control =
  "w-full rounded-sm border border-rule-strong bg-surface px-3 text-ui text-ink placeholder:text-ink-muted/80 " +
  "transition-[border-color,box-shadow] duration-150 hover:border-ink-muted " +
  "focus:border-brass-deep focus:outline-none focus:ring-2 focus:ring-brass-deep/20 " +
  "disabled:bg-canvas disabled:text-ink-muted aria-[invalid=true]:border-oxide";

export function Field({
  label,
  hint,
  error,
  children,
  optional,
  className,
}: {
  label: string;
  hint?: ReactNode;
  error?: string | null;
  optional?: boolean;
  className?: string;
  children: (props: { id: string; "aria-describedby"?: string; "aria-invalid"?: boolean }) => ReactNode;
}) {
  const id = useId();
  const hintId = hint ? `${id}-hint` : undefined;
  const errorId = error ? `${id}-error` : undefined;
  const describedBy = [hintId, errorId].filter(Boolean).join(" ") || undefined;
  return (
    <div className={cx("flex flex-col gap-1.5", className)}>
      <label htmlFor={id} className="text-ui-sm font-medium text-ink">
        {label}
        {optional ? <span className="ml-1.5 font-normal text-ink-muted">Optional</span> : null}
      </label>
      {children({ id, "aria-describedby": describedBy, "aria-invalid": error ? true : undefined })}
      {hint ? (
        <p id={hintId} className="text-meta text-ink-muted">
          {hint}
        </p>
      ) : null}
      {error ? (
        <p id={errorId} className="text-meta text-oxide" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}

export function Input({ className, ...rest }: ComponentProps<"input">) {
  return <input className={cx(control, "h-9", className)} {...rest} />;
}

export function Textarea({ className, ...rest }: ComponentProps<"textarea">) {
  return <textarea className={cx(control, "min-h-28 py-2 leading-relaxed", className)} {...rest} />;
}

export function Select({ className, children, ...rest }: ComponentProps<"select">) {
  return (
    <span className="relative block">
      <select className={cx(control, "h-9 appearance-none pr-8", className)} {...rest}>
        {children}
      </select>
      <svg
        aria-hidden="true"
        viewBox="0 0 20 20"
        className="pointer-events-none absolute right-2.5 top-1/2 size-4 -translate-y-1/2 text-ink-muted"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
      >
        <path d="m5 8 5 5 5-5" />
      </svg>
    </span>
  );
}

/** A segmented control for small option sets (filters, modes). */
export function Segmented<T extends string>({
  value,
  onChange,
  options,
  label,
  className,
}: {
  value: T;
  onChange: (value: T) => void;
  options: { value: T; label: ReactNode; count?: number }[];
  label: string;
  className?: string;
}) {
  const selected = Math.max(0, options.findIndex((o) => o.value === value));
  // Radio group keyboard pattern: one tab stop, arrow keys move the selection.
  const onKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    const step = e.key === "ArrowRight" || e.key === "ArrowDown" ? 1 : e.key === "ArrowLeft" || e.key === "ArrowUp" ? -1 : 0;
    if (!step && e.key !== "Home" && e.key !== "End") return;
    e.preventDefault();
    const n = options.length;
    const next = e.key === "Home" ? 0 : e.key === "End" ? n - 1 : (selected + step + n) % n;
    onChange(options[next].value);
    e.currentTarget.querySelectorAll<HTMLButtonElement>('[role="radio"]')[next]?.focus();
  };
  return (
    <div
      role="radiogroup"
      aria-label={label}
      onKeyDown={onKeyDown}
      className={cx("inline-flex rounded-sm border border-rule bg-surface p-0.5", className)}
    >
      {options.map((o, i) => {
        const active = o.value === value;
        return (
          <button
            key={o.value}
            type="button"
            role="radio"
            aria-checked={active}
            tabIndex={i === selected ? 0 : -1}
            onClick={() => onChange(o.value)}
            className={cx(
              "inline-flex h-7 shrink-0 items-center gap-1.5 whitespace-nowrap rounded-[2px] px-2.5 text-ui-sm transition-colors duration-150",
              active ? "bg-obsidian text-on-dark" : "text-ink-muted hover:bg-shade hover:text-ink",
            )}
          >
            {o.label}
            {o.count !== undefined ? (
              <span className={cx("tnum text-meta", active ? "text-on-dark-muted" : "text-ink-muted")}>{o.count}</span>
            ) : null}
          </button>
        );
      })}
    </div>
  );
}
