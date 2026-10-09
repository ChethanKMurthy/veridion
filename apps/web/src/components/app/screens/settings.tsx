"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { ErrorState, Notice, ScreenSkeleton } from "@/components/ui/feedback";
import { Field, Input, Select } from "@/components/ui/field";
import { useToast } from "@/components/ui/overlay";
import { ApiError } from "@/lib/api/client";
import { useApi, useClient, useInvalidate } from "@/lib/api/context";
import type { AuditEvent, Me, Member, OrgInfo } from "@/lib/api/types";
import { cx, dateTime, relative } from "@/lib/format";
import { PageHeader, Section } from "../shell";

function UsageMeter({ label, used, limit }: { label: string; used: number; limit: number | null }) {
  const ratio = limit ? Math.min(1, used / limit) : 0;
  return (
    <div>
      <div className="flex items-baseline justify-between text-ui-sm">
        <span className="text-ink-muted">{label}</span>
        <span className="tnum text-ink">
          {used}
          <span className="text-ink-muted"> / {limit ?? "unlimited"}</span>
        </span>
      </div>
      <div className="mt-1 h-1 overflow-hidden rounded-full bg-shade" aria-hidden="true">
        <div className={cx("h-full", ratio >= 0.9 ? "bg-oxide" : "bg-ink")} style={{ width: `${limit ? ratio * 100 : 0}%` }} />
      </div>
    </div>
  );
}

function AddMember() {
  const client = useClient();
  const invalidate = useInvalidate();
  const [form, setForm] = useState({ name: "", email: "", role: "analyst" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<ApiError | Error | null>(null);
  const [created, setCreated] = useState<{ email: string; temporary_password: string | null } | null>(null);
  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      const res = await client.send<{ email: string; temporary_password: string | null }>("POST", "/org/members", form);
      setCreated(res);
      setForm({ name: "", email: "", role: "analyst" });
      await invalidate("/org/members");
    } catch (err) {
      setError(err as Error);
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="rounded-sm border border-rule bg-surface p-4">
      <p className="text-ui font-medium text-ink">Add a member</p>
      <div className="mt-3 grid gap-3 sm:grid-cols-[1fr_1fr_10rem_auto] sm:items-end">
        <Field label="Name">{(p) => <Input {...p} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />}</Field>
        <Field label="Work email">{(p) => <Input {...p} type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />}</Field>
        <Field label="Role">
          {(p) => (
            <Select {...p} value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
              <option value="admin">Admin</option>
              <option value="analyst">Analyst</option>
              <option value="reviewer">Reviewer</option>
              <option value="viewer">Viewer</option>
            </Select>
          )}
        </Field>
        <Button variant="primary" onClick={submit} loading={busy} disabled={!form.name || !form.email}>
          Add
        </Button>
      </div>
      {error ? <Notice tone="danger" className="mt-3">{error.message}</Notice> : null}
      {created?.temporary_password ? (
        <Notice tone="success" className="mt-3" title="Member added">
          Share this temporary password with {created.email} through a secure channel. It is shown only once:{" "}
          <code className="font-mono text-ink">{created.temporary_password}</code>
        </Notice>
      ) : created ? (
        <Notice tone="success" className="mt-3">{created.email} already had an account and now has access.</Notice>
      ) : null}
      <p className="mt-3 text-meta text-ink-muted">
        Analysts upload documents and run assessments. Reviewers record decisions on findings and actions. Viewers read only.
      </p>
    </div>
  );
}

/** "Up to 3 companies, 10 documents and 150 pages per document." Unlimited items are named separately. */
function limitsSentence(plan: { max_companies: number | null; max_documents: number | null; max_pages_per_document: number | null }) {
  const items: [number | null, string][] = [
    [plan.max_companies, "companies"],
    [plan.max_documents, "documents"],
    [plan.max_pages_per_document, "pages per document"],
  ];
  const list = (parts: string[]) => (parts.length > 1 ? `${parts.slice(0, -1).join(", ")} and ${parts.at(-1)}` : parts[0]);
  const capped = items.filter(([n]) => n !== null).map(([n, label]) => `${n} ${label}`);
  const open = items.filter(([n]) => n === null).map(([, label]) => label);
  const sentences = [];
  if (capped.length) sentences.push(`Up to ${list(capped)}.`);
  if (open.length) sentences.push(`No limit on ${list(open)}.`);
  return sentences.join(" ");
}

export function SettingsScreen() {
  const client = useClient();
  const toast = useToast();
  const invalidate = useInvalidate();
  const { data: me } = useApi<Me>("/auth/me");
  const { data: org, error } = useApi<OrgInfo>("/org");
  const { data: members } = useApi<Member[]>("/org/members");
  const { data: events } = useApi<AuditEvent[]>("/org/audit-events", { limit: 60 });
  const [name, setName] = useState<string | null>(null);

  if (error) return <div className="p-6 lg:p-8"><ErrorState error={error} /></div>;
  if (!org || !me) return <ScreenSkeleton />;

  const isAdmin = me.role === "owner" || me.role === "admin";
  const plan = org.plan_details;
  const usage = org.usage as Record<string, number>;

  const rename = async () => {
    try {
      await client.send("PATCH", "/org", { name: name ?? org.name });
      await invalidate("/org", "/auth/me");
      toast("Organization renamed", "success");
      setName(null);
    } catch (err) {
      toast(err instanceof Error ? err.message : "Could not rename", "danger");
    }
  };

  return (
    <div className="px-4 py-6 sm:px-6 lg:px-8">
      <PageHeader title="Settings" description={`${org.name} · ${plan.name} plan`} />
      <div className="mt-8 grid gap-10 xl:grid-cols-2">
        <Section title="Organization">
          <div className="flex items-end gap-2">
            <Field label="Name" className="flex-1">
              {(p) => <Input {...p} value={name ?? org.name} disabled={!isAdmin} onChange={(e) => setName(e.target.value)} />}
            </Field>
            {isAdmin ? <Button onClick={rename} disabled={name === null || name.trim().length < 2}>Save</Button> : null}
          </div>
          <p className="mt-3 text-meta text-ink-muted">
            Model-assisted assessment is {org.llm_available ? "available" : "not configured"} on this deployment.
          </p>
        </Section>

        <Section title="Plan and usage" description={`Usage this month on the ${plan.name} plan.`}>
          <div className="space-y-3 rounded-sm border border-rule bg-surface p-4">
            <UsageMeter label="Assessment runs" used={usage.assessment_runs ?? 0} limit={plan.runs_per_month} />
            <UsageMeter label="Model-assisted runs" used={usage.hybrid_runs ?? 0} limit={plan.hybrid_runs_per_month} />
            <UsageMeter label="Members" used={members?.length ?? 0} limit={plan.max_seats} />
            <p className="pt-1 text-meta text-ink-muted">
              {limitsSentence(plan)} {usage.pages_processed ?? 0} pages processed this month.
            </p>
          </div>
        </Section>

        <Section title="Members" className="xl:col-span-2">
          <div className="overflow-x-auto rounded-sm border border-rule bg-surface">
            <table className="w-full min-w-[560px] text-left text-ui-sm">
              <thead>
                <tr className="border-b border-rule text-meta text-ink-muted">
                  <th className="px-4 py-2.5 font-medium">Name</th>
                  <th className="px-3 py-2.5 font-medium">Role</th>
                  <th className="px-4 py-2.5 font-medium">Last sign-in</th>
                </tr>
              </thead>
              <tbody>
                {(members ?? []).map((m) => (
                  <tr key={m.id} className="border-b border-rule last:border-0">
                    <td className="px-4 py-2.5">
                      <span className="block text-ink">{m.name}</span>
                      <span className="text-meta text-ink-muted">{m.email}</span>
                    </td>
                    <td className="px-3 py-2.5 capitalize text-ink-muted">{m.role}</td>
                    <td className="px-4 py-2.5 text-ink-muted">{relative(m.last_login_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {isAdmin ? <div className="mt-4"><AddMember /></div> : null}
        </Section>

        <Section title="Audit log" description="Security- and assessment-relevant events. Entries cannot be edited." className="xl:col-span-2">
          <ol className="divide-y divide-rule rounded-sm border border-rule bg-surface">
            {(events ?? []).map((e) => (
              <li key={e.id} className="grid gap-1 px-4 py-2.5 text-ui-sm sm:grid-cols-[12rem_1fr_10rem]">
                <span className="font-mono text-[0.75rem] text-ink">{e.action}</span>
                <span className="truncate text-ink-muted">
                  {e.actor_name ?? "System"}
                  {e.entity_type ? ` · ${e.entity_type}` : ""}
                  {Object.keys(e.data ?? {}).length ? ` · ${JSON.stringify(e.data).slice(0, 120)}` : ""}
                </span>
                <span className="text-meta text-ink-muted sm:text-right">{dateTime(e.created_at)}</span>
              </li>
            ))}
            {!events?.length ? <li className="px-4 py-3 text-ui-sm text-ink-muted">No events yet.</li> : null}
          </ol>
        </Section>

        <Section title="API access" className="xl:col-span-2">
          <p className="max-w-3xl text-ui-sm text-ink-muted">
            The REST API powers this interface and is documented at <a className="font-medium text-ink underline underline-offset-2" href="/api/docs">/api/docs</a>.
            Requests authenticate with the same session token as a bearer credential. Dedicated organization API keys are planned.
          </p>
        </Section>
      </div>
    </div>
  );
}
