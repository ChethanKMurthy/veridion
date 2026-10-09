import type { Metadata } from "next";
import { Suspense } from "react";
import { SignInForm } from "@/components/auth/auth-forms";

export const metadata: Metadata = { title: "Sign in" };

export default function SignInPage() {
  return (
    <>
      <h1 className="font-display text-[2rem] leading-tight text-ink">Sign in</h1>
      <p className="mb-8 mt-2 text-ui text-ink-muted">Continue to your evidence workspace.</p>
      <Suspense fallback={null}>
        <SignInForm />
      </Suspense>
    </>
  );
}
