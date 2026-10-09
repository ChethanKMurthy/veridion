"use client";

import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import { cx } from "@/lib/format";
import { Check, Close, Copy } from "./icons";

/**
 * Modal dialog and side drawer built on the native <dialog> element, which provides
 * focus trapping, Esc-to-close and an inert background without extra libraries.
 */
export function Dialog({
  open,
  onClose,
  title,
  description,
  children,
  footer,
  variant = "modal",
  width = "max-w-lg",
}: {
  open: boolean;
  onClose: () => void;
  title: ReactNode;
  description?: ReactNode;
  children: ReactNode;
  footer?: ReactNode;
  variant?: "modal" | "drawer";
  width?: string;
}) {
  const ref = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (open && !el.open) el.showModal();
    if (!open && el.open) el.close();
  }, [open]);

  return (
    <dialog
      ref={ref}
      onClose={onClose}
      onClick={(e) => {
        if (e.target === ref.current) onClose();
      }}
      className={cx(
        "m-0 max-h-dvh w-full bg-surface p-0 text-ink shadow-[var(--shadow-overlay)] backdrop:animate-fade-in",
        variant === "modal"
          ? cx("mx-auto mt-[10vh] max-h-[80vh] rounded-md border border-rule animate-rise-in", width)
          : "ml-auto h-dvh max-w-[min(var(--inspector-width),100vw)] border-l border-rule animate-panel-in",
      )}
      aria-labelledby="dialog-title"
    >
      {open ? (
        <div className={cx("flex flex-col", variant === "drawer" ? "h-full" : "max-h-[80vh]")}>
          <header className="flex items-start justify-between gap-4 border-b border-rule px-5 py-4">
            <div>
              <h2 id="dialog-title" className="text-[1rem] font-medium">
                {title}
              </h2>
              {description ? <p className="mt-1 text-ui-sm text-ink-muted">{description}</p> : null}
            </div>
            <button
              type="button"
              onClick={onClose}
              aria-label="Close"
              className="-mr-1 inline-flex size-8 items-center justify-center rounded-sm text-ink-muted hover:bg-shade hover:text-ink"
            >
              <Close />
            </button>
          </header>
          <div className="flex-1 overflow-y-auto px-5 py-5 scrollbar-quiet">{children}</div>
          {footer ? <footer className="flex justify-end gap-2 border-t border-rule px-5 py-3">{footer}</footer> : null}
        </div>
      ) : null}
    </dialog>
  );
}

type Toast = { id: number; message: ReactNode; tone: "default" | "success" | "danger" };
const ToastContext = createContext<(message: ReactNode, tone?: Toast["tone"]) => void>(() => {});

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const push = useCallback((message: ReactNode, tone: Toast["tone"] = "default") => {
    const id = Date.now() + Math.random();
    setToasts((t) => [...t, { id, message, tone }]);
    window.setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 4200);
  }, []);
  return (
    <ToastContext.Provider value={push}>
      {children}
      <div
        aria-live="polite"
        className="pointer-events-none fixed bottom-4 right-4 z-[var(--z-toast)] flex w-[min(380px,calc(100vw-2rem))] flex-col gap-2"
      >
        {toasts.map((t) => (
          <div
            key={t.id}
            className={cx(
              "pointer-events-auto flex items-start gap-2.5 rounded-sm border px-4 py-3 text-ui shadow-[var(--shadow-overlay)] animate-rise-in",
              t.tone === "danger" ? "border-oxide/30 bg-oxide-tint" : "border-rule bg-surface",
            )}
          >
            {t.tone === "success" ? <Check className="mt-0.5 text-forest" /> : null}
            <div>{t.message}</div>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  return useContext(ToastContext);
}

/** A monospace identifier with copy-to-clipboard. */
export function IdTag({ value, label, className }: { value: string; label?: string; className?: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      type="button"
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(value);
          setCopied(true);
          window.setTimeout(() => setCopied(false), 1400);
        } catch {
          /* clipboard unavailable */
        }
      }}
      className={cx(
        "group inline-flex max-w-full items-center gap-1.5 rounded-sm font-mono text-[0.7rem] text-ink-muted",
        "hover:text-ink",
        className,
      )}
      title={`Copy ${label ?? "identifier"}`}
      aria-label={`Copy ${label ?? "identifier"} ${value}`}
    >
      <span className="truncate">{value}</span>
      {copied ? <Check size={12} className="text-forest" /> : <Copy size={12} className="opacity-0 group-hover:opacity-100" />}
    </button>
  );
}
