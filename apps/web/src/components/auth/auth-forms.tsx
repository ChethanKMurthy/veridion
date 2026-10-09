"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { Notice } from "@/components/ui/feedback";
import { Field, Input } from "@/components/ui/field";
import { ApiError, HttpClient } from "@/lib/api/client";

const client = new HttpClient();

function safeNext(raw: string | null): string {
  if (!raw || !raw.startsWith("/app")) return "/app";
  return raw;
}

export function SignInForm() {
  const router = useRouter();
  const params = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await client.send("POST", "/auth/login", { email, password });
      router.replace(safeNext(params.get("next")));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign-in failed.");
      setBusy(false);
    }
  };

  return (
    <form onSubmit={submit} className="space-y-4" noValidate>
      <Field label="Work email">
        {(p) => <Input {...p} type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />}
      </Field>
      <Field label="Password">
        {(p) => (
          <Input {...p} type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} />
        )}
      </Field>
      {error ? <Notice tone="danger">{error}</Notice> : null}
      <Button type="submit" variant="primary" size="lg" className="w-full" loading={busy} disabled={!email || !password}>
        Sign in
      </Button>
      <p className="text-ui-sm text-ink-muted">
        New to Veridion?{" "}
        <Link href="/sign-up" className="font-medium text-ink underline underline-offset-2">
          Create a workspace
        </Link>{" "}
        or{" "}
        <Link href="/demo" className="font-medium text-ink underline underline-offset-2">
          explore the demo
        </Link>
        .
      </p>
    </form>
  );
}

export function SignUpForm() {
  const router = useRouter();
  const [form, setForm] = useState({ name: "", email: "", password: "", organization: "" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [closed, setClosed] = useState(false);
  const set = (k: keyof typeof form) => (e: { target: { value: string } }) => setForm((f) => ({ ...f, [k]: e.target.value }));
  const tooShort = form.password.length > 0 && form.password.length < 10;

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await client.send("POST", "/auth/register", form);
      router.replace("/app");
    } catch (err) {
      setClosed(err instanceof ApiError && err.code === "registration_closed");
      setError(err instanceof Error ? err.message : "Registration failed.");
      setBusy(false);
    }
  };

  return (
    <form onSubmit={submit} className="space-y-4" noValidate>
      <Field label="Your name">{(p) => <Input {...p} autoComplete="name" required value={form.name} onChange={set("name")} />}</Field>
      <Field label="Work email">
        {(p) => <Input {...p} type="email" autoComplete="email" required value={form.email} onChange={set("email")} />}
      </Field>
      <Field label="Organization" hint="Your firm or team. You can invite colleagues later.">
        {(p) => <Input {...p} autoComplete="organization" required value={form.organization} onChange={set("organization")} />}
      </Field>
      <Field label="Password" hint="At least 10 characters." error={tooShort ? "Use at least 10 characters." : null}>
        {(p) => <Input {...p} type="password" autoComplete="new-password" required value={form.password} onChange={set("password")} />}
      </Field>
      {error ? (
        <Notice tone={closed ? "info" : "danger"}>
          {error}
          {closed ? (
            <>
              {" "}
              <Link href="/request-access" className="font-medium text-ink underline underline-offset-2">
                Request access
              </Link>
            </>
          ) : null}
        </Notice>
      ) : null}
      <Button
        type="submit"
        variant="primary"
        size="lg"
        className="w-full"
        loading={busy}
        disabled={!form.name || !form.email || !form.organization || form.password.length < 10}
      >
        Create workspace
      </Button>
      <p className="text-meta leading-relaxed text-ink-muted">
        New workspaces start on the Explorer plan. By continuing you accept the{" "}
        <Link href="/legal/terms" className="underline underline-offset-2">terms</Link> and{" "}
        <Link href="/legal/privacy-notice" className="underline underline-offset-2">privacy notice</Link>.
      </p>
      <p className="text-ui-sm text-ink-muted">
        Already have an account?{" "}
        <Link href="/sign-in" className="font-medium text-ink underline underline-offset-2">
          Sign in
        </Link>
      </p>
    </form>
  );
}
