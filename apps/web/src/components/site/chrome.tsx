import Link from "next/link";
import type { ReactNode } from "react";
import { Wordmark } from "@/components/brand/logo";
import { ArrowRight } from "@/components/ui/icons";
import { cx } from "@/lib/format";
import { nav, site } from "@/lib/site";

export function SiteFooter() {
  const status =
    site.corporate.status === "incorporated" && site.corporate.legalName
      ? `${site.corporate.legalName}${site.corporate.registrationNumber ? ` · ${site.corporate.registrationNumber}` : ""}`
      : "Veridion is a product in development. Corporate registration details will be published on the Corporate information page once the operating entity is established.";
  return (
    <footer className="on-dark border-t border-rule-dark bg-obsidian text-on-dark print-hidden">
      <div className="mx-auto max-w-[1240px] px-4 pb-10 pt-16 sm:px-6 lg:px-8">
        <div className="grid gap-12 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,2fr)]">
          <div>
            <Link href="/" className="text-on-dark" aria-label="Veridion home">
              <Wordmark />
            </Link>
            <p className="mt-5 max-w-xs font-display text-[1.5rem] leading-snug text-on-dark">{site.tagline}</p>
          </div>
          <div className="grid grid-cols-2 gap-8 sm:grid-cols-4">
            {nav.footer.map((col) => (
              <div key={col.title}>
                <p className="text-ui-sm font-medium text-on-dark">{col.title}</p>
                <ul className="mt-4 space-y-2.5">
                  {col.links.map((l) => (
                    <li key={l.href}>
                      <Link href={l.href} className="text-ui-sm text-on-dark-muted transition-colors hover:text-on-dark">
                        {l.label}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
        <div className="mt-16 flex flex-col gap-4 border-t border-rule-dark pt-6 text-meta text-on-dark-muted lg:flex-row lg:items-start lg:justify-between">
          <p>© {site.year} Veridion. All rights reserved.</p>
          <p className="max-w-2xl lg:text-right">{status}</p>
        </div>
      </div>
    </footer>
  );
}

/** Dark opening section for inner pages. */
export function Masthead({
  title,
  lead,
  children,
  label,
  className,
}: {
  title: ReactNode;
  lead?: ReactNode;
  children?: ReactNode;
  label?: ReactNode;
  className?: string;
}) {
  return (
    <section className={cx("on-dark grain relative overflow-hidden bg-obsidian text-on-dark", className)}>
      <div className="mx-auto max-w-[1240px] px-4 pb-16 pt-16 sm:px-6 sm:pt-20 lg:px-8 lg:pb-20">
        {label ? <p className="mb-5 text-ui text-brass">{label}</p> : null}
        <h1 className="max-w-4xl font-display text-[clamp(2.4rem,5.2vw,4.4rem)] leading-[1.04] tracking-[-0.015em]">{title}</h1>
        {lead ? <p className="mt-6 max-w-2xl text-lead text-on-dark-muted">{lead}</p> : null}
        {children ? <div className="mt-9">{children}</div> : null}
      </div>
    </section>
  );
}

export function Container({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cx("mx-auto max-w-[1240px] px-4 sm:px-6 lg:px-8", className)}>{children}</div>;
}

export function CtaBand({
  title,
  body,
  primary = { href: "/demo", label: "Explore the platform" },
  secondary = { href: "/request-access", label: "Request access" },
}: {
  title: ReactNode;
  body?: ReactNode;
  primary?: { href: string; label: string };
  secondary?: { href: string; label: string } | null;
}) {
  return (
    <section className="on-dark bg-obsidian text-on-dark">
      <Container className="grid gap-10 py-20 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)] lg:items-end lg:py-28">
        <div>
          <h2 className="max-w-3xl font-display text-[clamp(2rem,4vw,3.4rem)] leading-[1.06] tracking-[-0.01em]">{title}</h2>
          {body ? <p className="mt-5 max-w-xl text-body text-on-dark-muted">{body}</p> : null}
        </div>
        <div className="flex flex-wrap gap-3 lg:justify-end">
          <Link
            href={primary.href}
            className="inline-flex h-12 items-center gap-2 rounded-sm bg-on-dark px-5 text-[0.95rem] font-medium text-obsidian transition-colors hover:bg-white"
          >
            {primary.label} <ArrowRight size={16} />
          </Link>
          {secondary ? (
            <Link
              href={secondary.href}
              className="inline-flex h-12 items-center rounded-sm border border-rule-dark-strong px-5 text-[0.95rem] text-on-dark transition-colors hover:border-on-dark-muted"
            >
              {secondary.label}
            </Link>
          ) : null}
        </div>
      </Container>
    </section>
  );
}

/** A legal or policy page body with an honest draft banner until legal review is complete. */
export function PolicyBody({ children, updated }: { children: ReactNode; updated?: string }) {
  return (
    <Container className="py-14 lg:py-20">
      <div className="grid gap-10 lg:grid-cols-[minmax(0,1fr)_16rem]">
        <div className="prose-veridion">{children}</div>
        <aside className="space-y-4 text-ui-sm text-ink-muted lg:sticky lg:top-24 lg:self-start">
          <p>Last updated {updated ?? site.legal.lastUpdated}.</p>
          {!site.legal.reviewed ? (
            <p className="rounded-sm bg-brass-tint px-3 py-2.5 text-ink">
              This document is a working draft written in plain language. It has not yet been reviewed by a lawyer and may change
              before Veridion offers a commercial service.
            </p>
          ) : null}
          <p>
            Questions? <Link href="/contact" className="font-medium text-ink underline underline-offset-2">Contact us</Link>.
          </p>
        </aside>
      </div>
    </Container>
  );
}
