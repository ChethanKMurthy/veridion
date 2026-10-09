"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Wordmark } from "@/components/brand/logo";
import { Close, Menu } from "@/components/ui/icons";
import { nav } from "@/lib/site";

export function SiteHeader() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [open]);

  return (
    <header className="on-dark sticky top-0 z-[var(--z-sticky)] border-b border-rule-dark bg-obsidian/95 text-on-dark backdrop-blur-[3px] print-hidden">
      <div className="mx-auto flex h-16 max-w-[1240px] items-center justify-between gap-6 px-4 sm:px-6 lg:px-8">
        <Link href="/" aria-label="Veridion home" className="text-on-dark">
          <Wordmark />
        </Link>
        <nav aria-label="Main" className="hidden lg:block">
          <ul className="flex items-center gap-7">
            {nav.primary.map((item) => (
              <li key={item.href}>
                <Link href={item.href} className="text-ui text-on-dark-muted transition-colors duration-150 hover:text-on-dark">
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
        <div className="hidden items-center gap-5 lg:flex">
          <Link href="/sign-in" className="text-ui text-on-dark-muted hover:text-on-dark">
            Sign in
          </Link>
          <Link
            href="/demo"
            className="inline-flex h-9 items-center rounded-sm bg-on-dark px-4 text-ui font-medium text-obsidian transition-colors hover:bg-white"
          >
            Explore the platform
          </Link>
        </div>
        <button
          type="button"
          onClick={() => setOpen(true)}
          aria-label="Open menu"
          aria-expanded={open}
          className="inline-flex size-10 items-center justify-center rounded-sm text-on-dark lg:hidden"
        >
          <Menu size={20} />
        </button>
      </div>
      {open ? (
        <div className="fixed inset-0 z-[var(--z-drawer)] flex flex-col bg-obsidian animate-fade-in lg:hidden" role="dialog" aria-modal="true" aria-label="Menu">
          <div className="flex h-16 items-center justify-between border-b border-rule-dark px-4 sm:px-6">
            <Link href="/" onClick={() => setOpen(false)} className="text-on-dark">
              <Wordmark />
            </Link>
            <button type="button" onClick={() => setOpen(false)} aria-label="Close menu" className="inline-flex size-10 items-center justify-center text-on-dark">
              <Close size={20} />
            </button>
          </div>
          <nav aria-label="Main" className="flex-1 overflow-y-auto px-4 py-6 sm:px-6">
            <ul className="space-y-1">
              {nav.primary.map((item) => (
                <li key={item.href}>
                  <Link href={item.href} onClick={() => setOpen(false)} className="block py-3 font-display text-[1.9rem] text-on-dark">
                    {item.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
          <div className="grid gap-3 border-t border-rule-dark px-4 py-5 sm:px-6">
            <Link href="/demo" onClick={() => setOpen(false)} className="inline-flex h-11 items-center justify-center rounded-sm bg-on-dark text-ui font-medium text-obsidian">
              Explore the platform
            </Link>
            <Link href="/sign-in" onClick={() => setOpen(false)} className="inline-flex h-11 items-center justify-center rounded-sm border border-rule-dark-strong text-ui text-on-dark">
              Sign in
            </Link>
          </div>
        </div>
      ) : null}
    </header>
  );
}
