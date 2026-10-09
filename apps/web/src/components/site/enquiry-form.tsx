"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useState, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { Notice } from "@/components/ui/feedback";
import { Field, Input, Select, Textarea } from "@/components/ui/field";
import { Check } from "@/components/ui/icons";
import { ApiError, HttpClient } from "@/lib/api/client";

export const ENQUIRY_KINDS: { value: string; label: string; hint?: string }[] = [
  { value: "demo_request", label: "Request a guided demonstration" },
  { value: "access_request", label: "Request product access" },
  { value: "sales", label: "Sales and pricing" },
  { value: "enterprise", label: "Enterprise and procurement" },
  { value: "support", label: "Technical support", hint: "Include the assessment or run ID if you have one." },
  { value: "billing", label: "Billing" },
  { value: "security", label: "Security report", hint: "Please do not include exploit details until we have replied with a secure channel." },
  { value: "privacy", label: "Privacy or personal data request" },
  { value: "partnership", label: "Partnerships" },
  { value: "media", label: "Media" },
  { value: "accessibility", label: "Accessibility" },
  { value: "complaint", label: "Complaint or escalation" },
  { value: "general", label: "Something else" },
];

const TOPIC_ALIASES: Record<string, string> = {
  demo: "demo_request",
  access: "access_request",
  sales: "sales",
  enterprise: "enterprise",
  support: "support",
  billing: "billing",
  security: "security",
  privacy: "privacy",
  partnerships: "partnership",
  media: "media",
  accessibility: "accessibility",
  complaints: "complaint",
};

const client = new HttpClient();

export function EnquiryForm({ defaultKind = "general", kinds, compact = false }: { defaultKind?: string; kinds?: string[]; compact?: boolean }) {
  const params = useSearchParams();
  const topic = params.get("topic");
  const plan = params.get("plan");
  const initial = (topic && TOPIC_ALIASES[topic]) || defaultKind;
  const options = kinds ? ENQUIRY_KINDS.filter((k) => kinds.includes(k.value)) : ENQUIRY_KINDS;
  const [form, setForm] = useState({
    kind: initial,
    name: "",
    email: "",
    organization: "",
    subject: plan ? `Interested in the ${plan} plan` : "",
    message: "",
    reference: "",
    website: "",
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState<string | null>(null);
  const set = (k: keyof typeof form) => (e: { target: { value: string } }) => setForm((f) => ({ ...f, [k]: e.target.value }));
  const kind = ENQUIRY_KINDS.find((k) => k.value === form.kind);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await client.send<{ reference: string }>("POST", "/public/enquiries", {
        ...form,
        organization: form.organization || null,
        subject: form.subject || null,
        reference: form.reference || null,
      });
      setDone(res.reference);
    } catch (err) {
      const status = (err as ApiError).status;
      setError(
        status === 429
          ? "Too many messages from this connection. Please try again in a few minutes."
          : status === 422
            ? "Please check the highlighted fields. The message needs at least 10 characters."
            : "The message could not be sent. Please try again shortly.",
      );
    } finally {
      setBusy(false);
    }
  };

  if (done) {
    return (
      <div className="rounded-sm border border-rule bg-surface p-6" role="status">
        <p className="flex items-center gap-2 text-[1.05rem] font-medium text-ink">
          <Check className="text-forest" /> Thank you — your message has been received.
        </p>
        <p className="mt-2 text-ui text-ink-muted">
          Your reference is <span className="font-mono text-ink">{done}</span>. We will reply to {form.email}. A small team reads every
          message, so it may take a few business days.
        </p>
      </div>
    );
  }

  return (
    <form onSubmit={submit} className="space-y-5" noValidate>
      {options.length > 1 ? (
        <Field label="What is this about?">
          {(p) => (
            <Select {...p} value={form.kind} onChange={set("kind")}>
              {options.map((k) => (
                <option key={k.value} value={k.value}>
                  {k.label}
                </option>
              ))}
            </Select>
          )}
        </Field>
      ) : null}
      <div className={compact ? "space-y-5" : "grid gap-5 sm:grid-cols-2"}>
        <Field label="Name">{(p) => <Input {...p} autoComplete="name" required value={form.name} onChange={set("name")} />}</Field>
        <Field label="Work email">
          {(p) => <Input {...p} type="email" autoComplete="email" required value={form.email} onChange={set("email")} />}
        </Field>
      </div>
      <Field label="Organization" optional>
        {(p) => <Input {...p} autoComplete="organization" value={form.organization} onChange={set("organization")} />}
      </Field>
      <Field label="Subject" optional>
        {(p) => <Input {...p} value={form.subject} onChange={set("subject")} />}
      </Field>
      <Field label="Message" hint={kind?.hint ?? "Tell us what you would like to assess or ask. Please do not send passwords or confidential documents."}>
        {(p) => <Textarea {...p} required rows={6} value={form.message} onChange={set("message")} />}
      </Field>
      {form.kind === "support" || form.kind === "complaint" ? (
        <Field label="Assessment or run ID" optional>
          {(p) => <Input {...p} value={form.reference} onChange={set("reference")} placeholder="e.g. run_01m4…" className="font-mono" />}
        </Field>
      ) : null}
      {/* Honeypot: hidden from people, filled in by bots. */}
      <div aria-hidden="true" className="absolute -left-[9999px] h-px w-px overflow-hidden">
        <label>
          Website
          <input tabIndex={-1} autoComplete="off" value={form.website} onChange={set("website")} />
        </label>
      </div>
      {error ? <Notice tone="danger">{error}</Notice> : null}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="max-w-md text-meta text-ink-muted">
          We use these details only to reply to you. See the <Link href="/legal/privacy-notice" className="underline underline-offset-2">privacy notice</Link>.
        </p>
        <Button type="submit" variant="primary" size="lg" loading={busy} disabled={!form.name || !form.email || form.message.trim().length < 10}>
          Send message
        </Button>
      </div>
    </form>
  );
}
