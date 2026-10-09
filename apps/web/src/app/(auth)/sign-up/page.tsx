import type { Metadata } from "next";
import { SignUpForm } from "@/components/auth/auth-forms";

export const metadata: Metadata = { title: "Create a workspace" };

export default function SignUpPage() {
  return (
    <>
      <h1 className="font-display text-[2rem] leading-tight text-ink">Create a workspace</h1>
      <p className="mb-8 mt-2 text-ui text-ink-muted">
        Upload disclosures, assess them against a versioned catalogue and trace every finding to its source.
      </p>
      <SignUpForm />
    </>
  );
}
