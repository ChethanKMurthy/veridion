import Link from "next/link";
import type { ComponentProps, ReactNode } from "react";
import { cx } from "@/lib/format";
import { Spinner } from "./icons";

type Variant = "primary" | "secondary" | "ghost" | "danger" | "inverse" | "inverse-outline";
type Size = "sm" | "md" | "lg";

const base =
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-sm font-medium select-none " +
  "transition-[background-color,border-color,color,box-shadow] duration-150 ease-[var(--ease-out-quart)] " +
  "disabled:opacity-50 aria-disabled:opacity-50 aria-disabled:pointer-events-none";

const variants: Record<Variant, string> = {
  primary: "bg-obsidian text-on-dark hover:bg-graphite-2 active:bg-graphite border border-obsidian",
  secondary: "bg-surface text-ink border border-rule-strong hover:border-ink-muted hover:bg-canvas active:bg-shade",
  ghost: "text-ink-muted hover:text-ink hover:bg-shade active:bg-rule border border-transparent",
  danger: "bg-surface text-oxide border border-rule-strong hover:border-oxide hover:bg-oxide-tint",
  inverse: "bg-on-dark text-obsidian border border-on-dark hover:bg-white active:bg-canvas",
  "inverse-outline": "text-on-dark border border-rule-dark-strong hover:border-on-dark-muted hover:bg-graphite",
};

const sizes: Record<Size, string> = {
  sm: "h-8 px-2.5 text-ui-sm",
  md: "h-9 px-3.5 text-ui",
  lg: "h-11 px-5 text-[0.9375rem]",
};

export function buttonClass(variant: Variant = "secondary", size: Size = "md", className?: string) {
  return cx(base, variants[variant], sizes[size], className);
}

type ButtonProps = ComponentProps<"button"> & {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
  icon?: ReactNode;
};

export function Button({
  variant = "secondary",
  size = "md",
  loading = false,
  icon,
  className,
  children,
  disabled,
  type = "button",
  ...rest
}: ButtonProps) {
  return (
    <button
      type={type}
      className={buttonClass(variant, size, className)}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...rest}
    >
      {loading ? <Spinner size={14} /> : icon}
      {children}
    </button>
  );
}

type LinkButtonProps = ComponentProps<typeof Link> & { variant?: Variant; size?: Size; icon?: ReactNode; iconAfter?: ReactNode };

export function LinkButton({ variant = "secondary", size = "md", className, icon, iconAfter, children, ...rest }: LinkButtonProps) {
  return (
    <Link className={buttonClass(variant, size, className)} {...rest}>
      {icon}
      {children}
      {iconAfter}
    </Link>
  );
}

export function IconButton({
  label,
  className,
  children,
  size = "md",
  ...rest
}: ComponentProps<"button"> & { label: string; size?: "sm" | "md" }) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      className={cx(
        "inline-flex items-center justify-center rounded-sm text-ink-muted transition-colors duration-150",
        "hover:bg-shade hover:text-ink active:bg-rule disabled:opacity-40",
        size === "sm" ? "size-7" : "size-8",
        className,
      )}
      {...rest}
    >
      {children}
    </button>
  );
}
