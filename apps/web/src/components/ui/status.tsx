import type { Status } from "@/lib/api/types";
import { STATUS, cx } from "@/lib/format";

const TONE: Record<Status, string> = {
  supported: "text-forest",
  partially_supported: "text-brass-deep",
  not_found: "text-ink-muted",
  conflicting: "text-oxide",
  human_review: "text-ink",
};

const TINT: Record<Status, string> = {
  supported: "bg-forest-tint",
  partially_supported: "bg-brass-tint",
  not_found: "bg-shade",
  conflicting: "bg-oxide-tint",
  human_review: "bg-review-tint",
};

/** Shape-coded glyph so status never depends on colour alone. */
export function StatusGlyph({ status, size = 12, className }: { status: Status; size?: number; className?: string }) {
  const common = { width: size, height: size, viewBox: "0 0 12 12", "aria-hidden": true as const };
  const cls = cx("shrink-0", TONE[status], className);
  switch (status) {
    case "supported":
      return (
        <svg {...common} className={cls}>
          <circle cx="6" cy="6" r="5" fill="currentColor" />
        </svg>
      );
    case "partially_supported":
      return (
        <svg {...common} className={cls}>
          <circle cx="6" cy="6" r="4.4" fill="none" stroke="currentColor" strokeWidth="1.3" />
          <path d="M6 1.6a4.4 4.4 0 0 1 0 8.8z" fill="currentColor" />
        </svg>
      );
    case "not_found":
      return (
        <svg {...common} className={cls}>
          <circle cx="6" cy="6" r="4.4" fill="none" stroke="currentColor" strokeWidth="1.3" />
        </svg>
      );
    case "conflicting":
      return (
        <svg {...common} className={cls}>
          <path d="M6 0.9 11.1 6 6 11.1 0.9 6z" fill="none" stroke="currentColor" strokeWidth="1.3" />
          <path d="m4.1 4.1 3.8 3.8M7.9 4.1 4.1 7.9" stroke="currentColor" strokeWidth="1.2" />
        </svg>
      );
    case "human_review":
      return (
        <svg {...common} className={cls}>
          <circle cx="6" cy="6" r="4.4" fill="none" stroke="currentColor" strokeWidth="1.3" strokeDasharray="2.2 1.4" />
          <circle cx="6" cy="6" r="1.6" fill="currentColor" />
        </svg>
      );
  }
}

export function StatusLabel({
  status,
  short = false,
  className,
  pill = false,
}: {
  status: Status;
  short?: boolean;
  className?: string;
  pill?: boolean;
}) {
  return (
    <span
      className={cx(
        "inline-flex items-center gap-1.5 whitespace-nowrap",
        TONE[status],
        pill && cx("rounded-sm px-1.5 py-0.5", TINT[status]),
        className,
      )}
      title={STATUS[status].description}
    >
      <StatusGlyph status={status} />
      <span className={status === "not_found" || status === "human_review" ? "text-ink-muted" : undefined}>
        {short ? STATUS[status].short : STATUS[status].label}
      </span>
    </span>
  );
}

export function statusTint(status: Status): string {
  return TINT[status];
}
