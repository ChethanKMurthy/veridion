"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Suspense, useState, type ReactNode } from "react";
import { Mark } from "@/components/brand/logo";
import { Building, Close, Grid, Layers, Menu, Settings, SignOut } from "@/components/ui/icons";
import { useApi, useClient, useHref } from "@/lib/api/context";
import type { Company, Me } from "@/lib/api/types";
import { cx } from "@/lib/format";

type NavItem = { href: string; label: string; icon: ReactNode; exact?: boolean; liveOnly?: boolean };

function useNavItems(): NavItem[] {
  const href = useHref();
  return [
    { href: href("/"), label: "Overview", icon: <Grid />, exact: true },
    { href: href("/companies"), label: "Companies", icon: <Building /> },
    { href: href("/requirements"), label: "Requirements", icon: <Layers /> },
    { href: href("/settings"), label: "Settings", icon: <Settings />, liveOnly: true },
  ];
}

function isActive(pathname: string, item: { href: string; exact?: boolean }) {
  return item.exact ? pathname === item.href : pathname === item.href || pathname.startsWith(`${item.href}/`);
}

function NavList({ pathname, onNavigate }: { pathname: string | null; onNavigate?: () => void }) {
  const client = useClient();
  const items = useNavItems().filter((i) => !(i.liveOnly && client.mode === "demo"));
  return (
    <ul className="space-y-px">
      {items.map((item) => {
        const active = pathname ? isActive(pathname, item) : false;
        return (
          <li key={item.href}>
            <Link
              href={item.href}
              onClick={onNavigate}
              aria-current={active ? "page" : undefined}
              className={cx(
                "flex h-8 items-center gap-2.5 rounded-sm px-2.5 text-ui transition-colors duration-150",
                active ? "bg-surface font-medium text-ink shadow-[inset_0_0_0_1px_var(--color-rule)]" : "text-ink-muted hover:bg-shade hover:text-ink",
              )}
            >
              <span className={active ? "text-ink" : "text-slate"}>{item.icon}</span>
              {item.label}
            </Link>
          </li>
        );
      })}
    </ul>
  );
}

function ActiveNavList({ onNavigate }: { onNavigate?: () => void }) {
  return <NavList pathname={usePathname()} onNavigate={onNavigate} />;
}

function CompanyList({ pathname, onNavigate }: { pathname: string | null; onNavigate?: () => void }) {
  const href = useHref();
  const { data } = useApi<Company[]>("/companies");
  if (!data?.length) return null;
  return (
    <div className="mt-7">
      <p className="px-2.5 text-meta font-medium text-ink-muted">Companies</p>
      <ul className="mt-1.5 space-y-px">
        {data.map((c) => {
          const base = href(`/companies/${c.id}`);
          const active = pathname ? pathname === base || pathname.startsWith(`${base}/`) : false;
          return (
            <li key={c.id}>
              <Link
                href={base}
                onClick={onNavigate}
                aria-current={active ? "page" : undefined}
                className={cx(
                  "flex h-8 items-center justify-between gap-2 rounded-sm px-2.5 text-ui-sm transition-colors duration-150",
                  active ? "bg-surface text-ink shadow-[inset_0_0_0_1px_var(--color-rule)]" : "text-ink-muted hover:bg-shade hover:text-ink",
                )}
              >
                <span className="truncate">{c.name}</span>
                {c.peer_ids?.length ? <span className="text-meta text-slate">focal</span> : null}
              </Link>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

function ActiveCompanyList({ onNavigate }: { onNavigate?: () => void }) {
  return <CompanyList pathname={usePathname()} onNavigate={onNavigate} />;
}

function SidebarBody({ me, onNavigate, footer }: { me: Me | null; onNavigate?: () => void; footer: ReactNode }) {
  const href = useHref();
  return (
    <div className="flex h-full flex-col">
      <div className="flex h-14 items-center gap-2.5 px-4">
        <Link href={href("/")} className="flex items-center gap-2.5 text-ink" onClick={onNavigate}>
          <Mark size={20} />
          <span className="font-serif text-[0.82rem] uppercase tracking-[0.2em]">Veridion</span>
        </Link>
      </div>
      <div className="px-4 pb-4">
        <p className="truncate text-ui-sm font-medium text-ink">{me?.organization.name ?? " "}</p>
        <p className="text-meta capitalize text-ink-muted">{me ? `${me.organization.plan} plan · ${me.role}` : " "}</p>
      </div>
      <nav aria-label="Workspace" className="flex-1 overflow-y-auto px-2 scrollbar-quiet">
        <Suspense fallback={<NavList pathname={null} />}>
          <ActiveNavList onNavigate={onNavigate} />
        </Suspense>
        <Suspense fallback={null}>
          <ActiveCompanyList onNavigate={onNavigate} />
        </Suspense>
      </nav>
      <div className="border-t border-rule px-3 py-3">{footer}</div>
    </div>
  );
}

export function AppShell({
  me,
  children,
  banner,
  footer,
}: {
  me: Me | null;
  children: ReactNode;
  banner?: ReactNode;
  footer: ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const href = useHref();
  return (
    <div className="flex min-h-dvh flex-col">
      {banner}
      <div className="flex flex-1">
        <aside
          className="sticky top-0 hidden h-dvh w-[var(--sidebar-width)] shrink-0 border-r border-rule bg-canvas lg:block"
          aria-label="Sidebar"
        >
          <SidebarBody me={me} footer={footer} />
        </aside>
        <div className="flex min-w-0 flex-1 flex-col">
          <div className="sticky top-0 z-[var(--z-sticky)] flex h-12 items-center justify-between border-b border-rule bg-canvas/95 px-4 backdrop-blur-[2px] lg:hidden">
            <Link href={href("/")} className="flex items-center gap-2 text-ink">
              <Mark size={18} />
              <span className="font-serif text-[0.78rem] uppercase tracking-[0.2em]">Veridion</span>
            </Link>
            <button
              type="button"
              onClick={() => setOpen(true)}
              aria-label="Open navigation"
              className="inline-flex size-9 items-center justify-center rounded-sm text-ink hover:bg-shade"
            >
              <Menu size={18} />
            </button>
          </div>
          <main id="main" className="min-w-0 flex-1">
            {children}
          </main>
        </div>
      </div>
      {open ? (
        <div className="fixed inset-0 z-[var(--z-drawer)] lg:hidden" role="dialog" aria-modal="true" aria-label="Navigation">
          <button type="button" aria-label="Close navigation" className="absolute inset-0 bg-obsidian/40 animate-fade-in" onClick={() => setOpen(false)} />
          <div className="absolute inset-y-0 left-0 w-[min(300px,85vw)] border-r border-rule bg-canvas animate-panel-in">
            <button
              type="button"
              onClick={() => setOpen(false)}
              aria-label="Close navigation"
              className="absolute right-2 top-3 inline-flex size-8 items-center justify-center rounded-sm text-ink-muted hover:bg-shade"
            >
              <Close />
            </button>
            <SidebarBody me={me} onNavigate={() => setOpen(false)} footer={footer} />
          </div>
        </div>
      ) : null}
    </div>
  );
}

export function UserFooter({ me, onSignOut }: { me: Me | null; onSignOut: () => void }) {
  return (
    <div className="flex items-center justify-between gap-2">
      <div className="min-w-0">
        <p className="truncate text-ui-sm text-ink">{me?.user.name ?? " "}</p>
        <p className="truncate text-meta text-ink-muted">{me?.user.email ?? " "}</p>
      </div>
      <button
        type="button"
        onClick={onSignOut}
        aria-label="Sign out"
        title="Sign out"
        className="inline-flex size-8 shrink-0 items-center justify-center rounded-sm text-ink-muted hover:bg-shade hover:text-ink"
      >
        <SignOut />
      </button>
    </div>
  );
}

/** Page header used by every product screen. */
export function PageHeader({
  title,
  eyebrow,
  description,
  actions,
  className,
  serif = false,
}: {
  title: ReactNode;
  eyebrow?: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
  className?: string;
  serif?: boolean;
}) {
  return (
    <header className={cx("flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between", className)}>
      <div className="min-w-0">
        {eyebrow ? <div className="mb-1.5 text-ui-sm text-ink-muted">{eyebrow}</div> : null}
        <h1 className={cx(serif ? "font-display text-[2rem] leading-tight tracking-[-0.01em]" : "text-[1.4rem] font-semibold tracking-[-0.01em]")}>
          {title}
        </h1>
        {description ? <div className="mt-1.5 max-w-3xl text-ui text-ink-muted">{description}</div> : null}
      </div>
      {actions ? <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div> : null}
    </header>
  );
}

export function Section({
  title,
  description,
  actions,
  children,
  className,
}: {
  title: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={cx("min-w-0", className)}>
      <div className="mb-3 flex items-end justify-between gap-3">
        <div>
          <h2 className="text-[0.95rem] font-semibold text-ink">{title}</h2>
          {description ? <p className="mt-0.5 text-ui-sm text-ink-muted">{description}</p> : null}
        </div>
        {actions ? <div className="flex shrink-0 items-center gap-2">{actions}</div> : null}
      </div>
      {children}
    </section>
  );
}
