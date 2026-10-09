"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { EmptyState, ErrorState, Notice, SkeletonRows } from "@/components/ui/feedback";
import { Field, Input, Select, Textarea } from "@/components/ui/field";
import { Plus } from "@/components/ui/icons";
import { Dialog } from "@/components/ui/overlay";
import { ApiError } from "@/lib/api/client";
import { useApi, useClient, useHref, useInvalidate } from "@/lib/api/context";
import type { Company } from "@/lib/api/types";
import { fiscalYearLabel, relative } from "@/lib/format";
import { PageHeader } from "../shell";
import { StatusDistribution } from "./company-overview";

const FYE = [
  ["12-31", "31 December (calendar year)"],
  ["03-31", "31 March"],
  ["06-30", "30 June"],
  ["09-30", "30 September"],
] as const;

function CreateCompany({ open, onClose }: { open: boolean; onClose: () => void }) {
  const client = useClient();
  const router = useRouter();
  const href = useHref();
  const invalidate = useInvalidate();
  const [form, setForm] = useState({ name: "", industry: "", country: "", fiscal_year_end: "12-31", website: "", description: "" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<ApiError | Error | null>(null);
  const set = (k: keyof typeof form) => (e: { target: { value: string } }) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      const created = await client.send<Company>("POST", "/companies", {
        ...form,
        industry: form.industry || null,
        country: form.country || null,
        website: form.website || null,
        description: form.description || null,
      });
      await invalidate("/companies", "/dashboard");
      onClose();
      router.push(href(`/companies/${created.id}/documents`));
    } catch (err) {
      setError(err as Error);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title="Add a company"
      description="The company you are assessing, or a peer to compare against."
      footer={
        <>
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button variant="primary" onClick={submit} loading={busy} disabled={!form.name.trim()}>Add company</Button>
        </>
      }
    >
      <div className="space-y-4">
        <Field label="Company name">{(p) => <Input {...p} value={form.name} onChange={set("name")} autoFocus />}</Field>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Industry" optional>{(p) => <Input {...p} value={form.industry} onChange={set("industry")} placeholder="e.g. Building materials" />}</Field>
          <Field label="Country" optional>{(p) => <Input {...p} value={form.country} onChange={set("country")} />}</Field>
        </div>
        <Field label="Financial year ends" hint="Used to align reporting periods when comparing companies.">
          {(p) => (
            <Select {...p} value={form.fiscal_year_end} onChange={set("fiscal_year_end")}>
              {FYE.map(([v, l]) => (
                <option key={v} value={v}>{l}</option>
              ))}
            </Select>
          )}
        </Field>
        <Field label="Website" optional>{(p) => <Input {...p} value={form.website} onChange={set("website")} placeholder="https://" />}</Field>
        <Field label="Notes" optional>{(p) => <Textarea {...p} value={form.description} onChange={set("description")} rows={3} />}</Field>
        {error ? (
          <Notice tone={(error as ApiError).code === "plan_limit" ? "warning" : "danger"}>
            {error.message}{" "}
            {(error as ApiError).code === "plan_limit" ? <Link href="/pricing" className="font-medium text-ink underline">Compare plans</Link> : null}
            {(error as ApiError).code === "demo_read_only" ? <Link href="/request-access" className="font-medium text-ink underline">Request access</Link> : null}
          </Notice>
        ) : null}
      </div>
    </Dialog>
  );
}

export function CompaniesScreen() {
  const href = useHref();
  const [creating, setCreating] = useState(false);
  const { data, error, mutate } = useApi<Company[]>("/companies");
  return (
    <div className="px-4 py-6 sm:px-6 lg:px-8">
      <PageHeader
        title="Companies"
        description="Each company keeps its own documents, assessments, peers and actions."
        actions={<Button variant="primary" size="sm" icon={<Plus size={14} />} onClick={() => setCreating(true)}>Add company</Button>}
      />
      <div className="mt-6 overflow-x-auto rounded-sm border border-rule bg-surface scrollbar-quiet">
        {error ? (
          <div className="p-4"><ErrorState error={error} retry={() => mutate()} /></div>
        ) : !data ? (
          <div className="px-4"><SkeletonRows rows={4} /></div>
        ) : !data.length ? (
          <EmptyState className="m-4 border-none" title="No companies yet" action={<Button variant="primary" icon={<Plus size={14} />} onClick={() => setCreating(true)}>Add your first company</Button>}>
            Add the company you are assessing, then upload its annual and sustainability reports.
          </EmptyState>
        ) : (
          <table className="w-full min-w-[820px] text-left text-ui-sm">
            <thead>
              <tr className="border-b border-rule text-meta text-ink-muted">
                <th scope="col" className="px-4 py-2.5 font-medium">Company</th>
                <th scope="col" className="px-3 py-2.5 font-medium">Financial year</th>
                <th scope="col" className="px-3 py-2.5 text-right font-medium">Documents</th>
                <th scope="col" className="px-3 py-2.5 font-medium">Latest assessment</th>
                <th scope="col" className="px-4 py-2.5 font-medium">Assessed</th>
              </tr>
            </thead>
            <tbody>
              {data.map((c) => (
                <tr key={c.id} className="border-b border-rule align-top last:border-0 hover:bg-canvas">
                  <td className="px-4 py-3">
                    <Link href={href(`/companies/${c.id}`)} className="font-medium text-ink hover:underline">
                      {c.name}
                    </Link>
                    <span className="block text-meta text-ink-muted">
                      {[c.industry, c.country].filter(Boolean).join(" · ") || "—"}
                      {c.is_sample ? " · fictional sample" : ""}
                    </span>
                  </td>
                  <td className="px-3 py-3 text-ink-muted">{fiscalYearLabel(c.fiscal_year_end)}</td>
                  <td className="tnum px-3 py-3 text-right text-ink-muted">
                    {c.documents_ready ?? 0}/{c.document_count ?? 0}
                  </td>
                  <td className="w-72 px-3 py-3">
                    {c.latest_run ? (
                      <Link href={href(`/companies/${c.id}/evidence?run=${c.latest_run.id}`)} className="block">
                        <StatusDistribution summary={c.latest_run.summary} />
                      </Link>
                    ) : (
                      <span className="text-ink-muted">Not assessed</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-ink-muted">{c.latest_run ? relative(c.latest_run.finished_at) : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
      <CreateCompany key={String(creating)} open={creating} onClose={() => setCreating(false)} />
    </div>
  );
}
