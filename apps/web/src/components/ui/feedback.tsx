import type { ReactNode } from "react";
import { cx } from "@/lib/format";
import { Alert, Info } from "./icons";

export function Skeleton({ className }: { className?: string }) {
  return <div className={cx("animate-pulse rounded-sm bg-shade", className)} aria-hidden="true" />;
}

export function SkeletonRows({ rows = 6, className }: { rows?: number; className?: string }) {
  return (
    <div className={cx("divide-y divide-rule", className)} aria-busy="true" aria-label="Loading">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex items-center gap-4 py-3">
          <Skeleton className="h-3 w-16" />
          <Skeleton className="h-3 flex-1" />
          <Skeleton className="h-3 w-24" />
        </div>
      ))}
    </div>
  );
}

export function ScreenSkeleton() {
  return (
    <div className="space-y-6 p-6 lg:p-8" aria-busy="true" aria-label="Loading">
      <Skeleton className="h-3 w-40" />
      <Skeleton className="h-8 w-80 max-w-full" />
      <div className="grid gap-4 sm:grid-cols-3">
        <Skeleton className="h-20" />
        <Skeleton className="h-20" />
        <Skeleton className="h-20" />
      </div>
      <SkeletonRows rows={8} />
    </div>
  );
}

/** Empty states teach the next step rather than saying "nothing here". */
export function EmptyState({
  title,
  children,
  action,
  className,
}: {
  title: string;
  children?: ReactNode;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cx("rounded-sm border border-dashed border-rule-strong px-6 py-10 text-center", className)}>
      <h3 className="text-[0.95rem] font-medium text-ink">{title}</h3>
      {children ? <div className="mx-auto mt-2 max-w-md text-ui text-ink-muted">{children}</div> : null}
      {action ? <div className="mt-5 flex justify-center gap-2">{action}</div> : null}
    </div>
  );
}

export function ErrorState({ error, retry, className }: { error: unknown; retry?: () => void; className?: string }) {
  const status = (error as { status?: number })?.status;
  const message =
    error instanceof Error ? error.message : typeof error === "string" ? error : "Something went wrong.";
  return (
    <div role="alert" className={cx("rounded-sm border border-oxide/30 bg-oxide-tint px-5 py-4 text-ui", className)}>
      <div className="flex items-start gap-3">
        <Alert className="mt-0.5 text-oxide" />
        <div className="flex-1">
          <p className="font-medium text-ink">{status === 404 ? "Not found" : "This view could not be loaded"}</p>
          <p className="mt-1 text-ink-muted">{message}</p>
          {retry ? (
            <button type="button" onClick={retry} className="mt-3 text-ui-sm font-medium text-ink underline underline-offset-4">
              Try again
            </button>
          ) : null}
        </div>
      </div>
    </div>
  );
}

/** Inline notice. Tinted background with a leading icon — never a coloured side stripe. */
export function Notice({
  tone = "info",
  title,
  children,
  className,
  action,
}: {
  tone?: "info" | "warning" | "danger" | "success";
  title?: ReactNode;
  children?: ReactNode;
  className?: string;
  action?: ReactNode;
}) {
  const tones = {
    info: "bg-shade text-ink",
    warning: "bg-brass-tint text-ink",
    danger: "bg-oxide-tint text-ink",
    success: "bg-forest-tint text-ink",
  } as const;
  const iconTone = { info: "text-ink-muted", warning: "text-brass-deep", danger: "text-oxide", success: "text-forest" } as const;
  return (
    <div className={cx("flex items-start gap-3 rounded-sm px-4 py-3 text-ui", tones[tone], className)}>
      {tone === "info" ? (
        <Info className={cx("mt-0.5 shrink-0", iconTone[tone])} />
      ) : (
        <Alert className={cx("mt-0.5 shrink-0", iconTone[tone])} />
      )}
      <div className="min-w-0 flex-1">
        {title ? <p className="font-medium">{title}</p> : null}
        {children ? <div className={cx("text-ink-muted", title ? "mt-0.5" : undefined)}>{children}</div> : null}
      </div>
      {action ? <div className="shrink-0">{action}</div> : null}
    </div>
  );
}
