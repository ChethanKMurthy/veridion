"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState, useSyncExternalStore, type ReactNode } from "react";
import { ArrowRight, Check, ChevronDown, Close } from "@/components/ui/icons";
import { ToastProvider } from "@/components/ui/overlay";
import { HttpClient } from "@/lib/api/client";
import { DataProvider, useApi, useClient, useHref } from "@/lib/api/context";
import { SnapshotClient, type DemoManifest } from "@/lib/api/snapshot";
import type { FindingSummary, Me, Run } from "@/lib/api/types";
import { cx } from "@/lib/format";
import { AppShell, UserFooter } from "./shell";

function LiveInner({ children }: { children: ReactNode }) {
  const router = useRouter();
  const client = useClient();
  const { data: me, error } = useApi<Me>("/auth/me");

  useEffect(() => {
    if ((error as { status?: number })?.status === 401) {
      const next = typeof window !== "undefined" ? window.location.pathname + window.location.search : "/app";
      router.replace(`/sign-in?next=${encodeURIComponent(next)}`);
    }
  }, [error, router]);

  const signOut = async () => {
    try {
      await client.send("POST", "/auth/logout");
    } finally {
      router.replace("/sign-in");
    }
  };

  return (
    <AppShell me={me ?? null} footer={<UserFooter me={me ?? null} onSignOut={signOut} />}>
      {children}
    </AppShell>
  );
}

export function LiveWorkspace({ children }: { children: ReactNode }) {
  const client = useMemo(() => new HttpClient(), []);
  return (
    <DataProvider client={client}>
      <ToastProvider>
        <LiveInner>{children}</LiveInner>
      </ToastProvider>
    </DataProvider>
  );
}

// ---------------------------------------------------------------------------------------------
// Demo
// ---------------------------------------------------------------------------------------------

const SCENARIO_KEY = "veridion.demo.scenario";

type Step = { id: string; title: string; detail: string; href: string };

function useScenario(manifest: DemoManifest | undefined): Step[] {
  const href = useHref();
  const focal = manifest?.focal_company_id;
  const { data: runs } = useApi<Run[]>(focal ? `/companies/${focal}/runs` : null);
  const latest = runs?.find((r) => r.status === "completed");
  const { data: findings } = useApi<FindingSummary[]>(latest ? `/runs/${latest.id}/findings` : null);
  const conflict = findings?.find((f) => f.status === "conflicting") ?? findings?.find((f) => f.status !== "supported");
  if (!focal) return [];
  const base = href(`/companies/${focal}`);
  return [
    {
      id: "gap",
      title: "Find a disclosure gap",
      detail: "Filter the Evidence Explorer to requirements that are not fully supported.",
      href: `${base}/evidence?status=gaps`,
    },
    {
      id: "evidence",
      title: "Inspect the evidence",
      detail: "Open the conflicting energy figure and follow the trail to both source pages.",
      href: conflict ? `${base}/evidence?finding=${conflict.id}` : `${base}/evidence`,
    },
    {
      id: "peer",
      title: "Compare a peer",
      detail: "See how Scope 1 emissions compare once periods, units and boundaries are checked.",
      href: `${base}/peers`,
    },
    {
      id: "action",
      title: "Take a remediation action",
      detail: "Assign an owner to the highest-priority action and mark it in progress.",
      href: `${base}/actions`,
    },
  ];
}

const scenarioListeners = new Set<() => void>();

function subscribeScenario(listener: () => void) {
  scenarioListeners.add(listener);
  return () => scenarioListeners.delete(listener);
}

/** Raw stored value (a string, so React can compare snapshots cheaply). */
function scenarioSnapshot(): string {
  try {
    return window.sessionStorage.getItem(SCENARIO_KEY) ?? "[]";
  } catch {
    return "[]";
  }
}

function writeDone(ids: string[]) {
  try {
    window.sessionStorage.setItem(SCENARIO_KEY, JSON.stringify(ids));
  } catch {
    /* storage unavailable: progress is simply not remembered */
  }
  scenarioListeners.forEach((l) => l());
}

function parseDone(raw: string): string[] {
  try {
    const value = JSON.parse(raw);
    return Array.isArray(value) ? value : [];
  } catch {
    return [];
  }
}

function DemoBanner({ manifest }: { manifest: DemoManifest | undefined }) {
  const steps = useScenario(manifest);
  const [open, setOpen] = useState(false);
  const raw = useSyncExternalStore(subscribeScenario, scenarioSnapshot, () => "[]");
  const done = useMemo(() => parseDone(raw), [raw]);

  const mark = (id: string) => {
    writeDone(Array.from(new Set([...done, id])));
    setOpen(false);
  };

  return (
    <div className="on-dark border-b border-rule-dark bg-obsidian text-on-dark print-hidden">
      <div className="flex flex-wrap items-center justify-between gap-x-6 gap-y-2 px-4 py-2.5 lg:px-6">
        <p className="text-ui-sm text-on-dark-muted">
          <span className="font-medium text-on-dark">Interactive demo.</span> Fictional companies and documents, assessed by the
          Veridion engine{manifest?.llm_model ? <> (rules + {manifest.llm_model})</> : null}. Changes stay in this browser tab.
        </p>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setOpen((o) => !o)}
            aria-expanded={open}
            className="inline-flex h-8 items-center gap-2 rounded-sm border border-rule-dark-strong px-3 text-ui-sm text-on-dark hover:bg-graphite"
          >
            Guided scenario
            <span className="tnum text-on-dark-muted">
              {done.length}/{steps.length || 4}
            </span>
            <ChevronDown className={cx("transition-transform duration-200", open && "rotate-180")} />
          </button>
          <Link
            href="/request-access"
            className="inline-flex h-8 items-center gap-1.5 rounded-sm bg-on-dark px-3 text-ui-sm font-medium text-obsidian hover:bg-white"
          >
            Request access
          </Link>
        </div>
      </div>
      {open ? (
        <div className="border-t border-rule-dark px-4 pb-4 pt-3 animate-fade-in lg:px-6">
          <div className="flex items-start justify-between gap-4">
            <p className="max-w-2xl text-ui-sm text-on-dark-muted">
              Four steps, about five minutes. Each one opens the screen where the work happens.
            </p>
            <button type="button" onClick={() => setOpen(false)} aria-label="Close guided scenario" className="text-on-dark-muted hover:text-on-dark">
              <Close />
            </button>
          </div>
          <ol className="mt-3 grid gap-px overflow-hidden rounded-sm border border-rule-dark bg-rule-dark sm:grid-cols-2 xl:grid-cols-4">
            {steps.map((s, i) => {
              const complete = done.includes(s.id);
              return (
                <li key={s.id} className="bg-obsidian">
                  <Link href={s.href} onClick={() => mark(s.id)} className="group flex h-full flex-col gap-1.5 p-4 hover:bg-graphite">
                    <span className="flex items-center gap-2 text-meta text-on-dark-muted">
                      <span
                        className={cx(
                          "inline-flex size-5 items-center justify-center rounded-full border text-[0.68rem] tnum",
                          complete ? "border-brass bg-brass text-obsidian" : "border-rule-dark-strong",
                        )}
                      >
                        {complete ? <Check size={11} /> : i + 1}
                      </span>
                      Step {i + 1}
                    </span>
                    <span className="flex items-center gap-1.5 text-ui font-medium text-on-dark">
                      {s.title}
                      <ArrowRight size={14} className="opacity-0 transition-opacity group-hover:opacity-100" />
                    </span>
                    <span className="text-ui-sm text-on-dark-muted">{s.detail}</span>
                  </Link>
                </li>
              );
            })}
          </ol>
        </div>
      ) : null}
    </div>
  );
}

function DemoInner({ children }: { children: ReactNode }) {
  const { data: me } = useApi<Me>("/auth/me");
  const [manifest, setManifest] = useState<DemoManifest>();
  useEffect(() => {
    fetch("/demo/manifest.json")
      .then((r) => (r.ok ? r.json() : undefined))
      .then(setManifest)
      .catch(() => undefined);
  }, []);
  const footer = (
    <div className="space-y-2">
      <p className="text-meta text-ink-muted">Viewing the demo workspace as a guest. Nothing you do here is saved.</p>
      <Link href="/" className="text-ui-sm font-medium text-ink underline underline-offset-4">
        Back to the website
      </Link>
    </div>
  );
  return (
    <AppShell me={me ?? null} banner={<DemoBanner manifest={manifest} />} footer={footer}>
      {children}
    </AppShell>
  );
}

export function DemoWorkspace({ children }: { children: ReactNode }) {
  const client = useMemo(() => new SnapshotClient(), []);
  return (
    <DataProvider client={client}>
      <ToastProvider>
        <DemoInner>{children}</DemoInner>
      </ToastProvider>
    </DataProvider>
  );
}

export function useDemoFocal(): string | undefined {
  const [manifest, setManifest] = useState<DemoManifest>();
  const client = useClient();
  useEffect(() => {
    if (client.mode !== "demo") return;
    fetch("/demo/manifest.json")
      .then((r) => (r.ok ? r.json() : undefined))
      .then(setManifest)
      .catch(() => undefined);
  }, [client.mode]);
  return manifest?.focal_company_id ?? undefined;
}
