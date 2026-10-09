import { cx } from "@/lib/format";

/**
 * The Veridion mark: an evidence trail as a seal. Two source points converge on a
 * single verified point inside a square frame — claim, evidence, conclusion.
 */
export function Mark({ size = 24, className, title }: { size?: number; className?: string; title?: string }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      className={className}
      role={title ? "img" : undefined}
      aria-hidden={title ? undefined : true}
    >
      {title ? <title>{title}</title> : null}
      <rect x="1.75" y="1.75" width="28.5" height="28.5" rx="1" stroke="currentColor" strokeWidth="1.5" />
      <path d="M9 10.5 16 23l7-12.5" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
      <circle cx="9" cy="10.5" r="2.1" fill="currentColor" />
      <circle cx="23" cy="10.5" r="2.1" fill="currentColor" />
      <circle cx="16" cy="23" r="2.75" fill="currentColor" />
    </svg>
  );
}

export function Wordmark({ className }: { className?: string }) {
  return (
    <span className={cx("inline-flex items-center gap-2.5", className)}>
      <Mark size={22} />
      <span className="font-serif text-[0.95rem] uppercase tracking-[0.2em]">Veridion</span>
    </span>
  );
}
