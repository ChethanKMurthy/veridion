"use client";

import Link from "next/link";
import { useParams, usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { ErrorState, Skeleton } from "@/components/ui/feedback";
import { useApi, useHref } from "@/lib/api/context";
import type { Company } from "@/lib/api/types";
import { cx, fiscalYearLabel } from "@/lib/format";

const TABS = [
  { path: "", label: "Intelligence" },
  { path: "/evidence", label: "Evidence" },
  { path: "/documents", label: "Documents" },
  { path: "/peers", label: "Peers" },
  { path: "/actions", label: "Actions" },
  { path: "/history", label: "History" },
];

export function useCompanyId(): string {
  const params = useParams<{ companyId: string }>();
  return params.companyId;
}

/** Company header and section tabs shared by every company screen. */
export function CompanyFrame({ children }: { children: ReactNode }) {
  const companyId = useCompanyId();
  const pathname = usePathname();
  const href = useHref();
  const { data: company, error } = useApi<Company>(`/companies/${companyId}`);
  const base = href(`/companies/${companyId}`);

  return (
    <div className="flex min-h-full flex-col">
      <div className="border-b border-rule bg-canvas px-4 pt-5 sm:px-6 lg:px-8">
        <nav aria-label="Breadcrumb" className="text-ui-sm text-ink-muted">
          <Link href={href("/companies")} className="hover:text-ink">
            Companies
          </Link>
          <span className="mx-1.5 text-slate" aria-hidden="true">/</span>
          <span className="text-ink">{company?.name ?? "…"}</span>
        </nav>
        {error ? (
          <ErrorState error={error} className="my-4" />
        ) : (
          <div className="mt-2 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
            <div className="min-w-0">
              {company ? (
                <h1 className="font-display text-[1.9rem] leading-tight tracking-[-0.01em] text-ink">{company.name}</h1>
              ) : (
                <Skeleton className="h-8 w-72" />
              )}
              <p className="mt-1 text-ui-sm text-ink-muted">
                {company ? (
                  <>
                    {[company.industry, company.country, fiscalYearLabel(company.fiscal_year_end)].filter(Boolean).join(" · ")}
                    {company.is_sample ? <span className="ml-2 rounded-[2px] bg-brass-tint px-1.5 py-0.5 text-meta text-brass-deep">Fictional sample company</span> : null}
                  </>
                ) : (
                  " "
                )}
              </p>
            </div>
          </div>
        )}
        <nav aria-label="Company sections" className="-mb-px mt-4 flex gap-1 overflow-x-auto no-scrollbar">
          {TABS.map((t) => {
            const target = `${base}${t.path}`;
            const active = t.path === "" ? pathname === base : pathname?.startsWith(target);
            return (
              <Link
                key={t.path}
                href={target}
                aria-current={active ? "page" : undefined}
                className={cx(
                  "relative shrink-0 px-3 pb-2.5 pt-1 text-ui transition-colors duration-150",
                  active ? "font-medium text-ink" : "text-ink-muted hover:text-ink",
                )}
              >
                {t.label}
                <span
                  aria-hidden="true"
                  className={cx("absolute inset-x-3 bottom-0 h-px transition-colors", active ? "bg-ink" : "bg-transparent")}
                />
              </Link>
            );
          })}
        </nav>
      </div>
      <div className="min-w-0 flex-1">{children}</div>
    </div>
  );
}
