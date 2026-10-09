import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { Container, Masthead } from "@/components/site/chrome";
import { EnquiryForm } from "@/components/site/enquiry-form";

export const metadata: Metadata = {
  title: "Request access",
  description: "Request access to Veridion or a guided demonstration with your own material.",
};

export default function RequestAccessPage() {
  return (
    <>
      <Masthead
        title="Request access"
        lead="Tell us what you review and what you would like to test. Pilot users get a Professional workspace and a direct line to the team building the product."
      />
      <Container className="grid gap-14 py-16 lg:grid-cols-[minmax(0,0.8fr)_minmax(0,1.2fr)] lg:py-24">
        <div className="space-y-8">
          <div>
            <h2 className="text-[1.05rem] font-semibold text-ink">Three ways in</h2>
            <dl className="mt-4 divide-y divide-rule border-y border-rule">
              <div className="py-4">
                <dt className="text-ui font-medium text-ink">Explore the demo</dt>
                <dd className="mt-1 text-ui-sm text-ink-muted">
                  Immediate access to a workspace with fictional companies. <Link href="/demo" className="text-ink underline underline-offset-2">Open the demo</Link>.
                </dd>
              </div>
              <div className="py-4">
                <dt className="text-ui font-medium text-ink">Create an Explorer workspace</dt>
                <dd className="mt-1 text-ui-sm text-ink-muted">
                  Upload your own PDFs within the Explorer limits. <Link href="/sign-up" className="text-ink underline underline-offset-2">Create a workspace</Link>.
                </dd>
              </div>
              <div className="py-4">
                <dt className="text-ui font-medium text-ink">Join the pilot</dt>
                <dd className="mt-1 text-ui-sm text-ink-muted">A guided walkthrough and a Professional workspace for recurring assessments. Use the form.</dd>
              </div>
            </dl>
          </div>
          <p className="text-ui-sm text-ink-muted">
            If you share example documents during a pilot, use publicly available or appropriately anonymised material unless we have
            agreed otherwise in writing.
          </p>
        </div>
        <div className="rounded-sm border border-rule bg-surface p-6">
          <Suspense fallback={null}>
            <EnquiryForm defaultKind="access_request" kinds={["access_request", "demo_request", "enterprise"]} />
          </Suspense>
        </div>
      </Container>
    </>
  );
}
