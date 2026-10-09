import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { Container, Masthead } from "@/components/site/chrome";
import { EnquiryForm } from "@/components/site/enquiry-form";
import { site } from "@/lib/site";

export const metadata: Metadata = {
  title: "Contact",
  description: "Sales, support, security, privacy and general enquiries for Veridion.",
};

const routes: [string, string, React.ReactNode][] = [
  ["Help centre", "Common questions, account help and troubleshooting", <Link key="h" href="/help">Open the help centre</Link>],
  ["Documentation", "Guides, concepts, limitations and the API", <Link key="d" href="/documentation">Read the documentation</Link>],
  ["Technical support", "Failed imports, exports and application errors", <Link key="s" href="/contact?topic=support">Choose “Technical support” below</Link>],
  ["Sales and enterprise", "Pricing, demonstrations, procurement and security questionnaires", <Link key="e" href="/contact?topic=enterprise">Choose “Enterprise” below</Link>],
  ["Security", "Responsible reporting of vulnerabilities", <Link key="v" href="/trust/security#reporting">How to report a vulnerability</Link>],
  ["Privacy", "Personal data requests and privacy questions", <Link key="p" href="/contact?topic=privacy">Choose “Privacy” below</Link>],
  ["Complaints", "Concerns that have not been resolved through other routes", <Link key="c" href="/contact?topic=complaints">Choose “Complaint or escalation” below</Link>],
  ["Service status", "Availability and incidents", <span key="st">A status page will be published when Veridion operates a production service.</span>],
];

export default function ContactPage() {
  return (
    <>
      <Masthead title="Contact" lead={site.support.commitment} />
      <Container className="grid gap-14 py-16 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)] lg:py-24">
        <section>
          <h2 className="font-display text-[1.9rem] text-ink">Where to go</h2>
          <dl className="mt-6 divide-y divide-rule border-y border-rule">
            {routes.map(([title, desc, link]) => (
              <div key={title} className="py-4">
                <dt className="text-ui font-medium text-ink">{title}</dt>
                <dd className="mt-0.5 text-ui-sm text-ink-muted">{desc}</dd>
                <dd className="mt-1 text-ui-sm text-ink [&_a]:underline [&_a]:decoration-rule-strong [&_a]:underline-offset-2">{link}</dd>
              </div>
            ))}
          </dl>
          <p className="mt-6 text-ui-sm text-ink-muted">
            Please never send passwords, authentication codes or confidential company documents through this form. If we need
            documents to help you, we will arrange a secure route.
          </p>
        </section>
        <section aria-labelledby="form-title">
          <h2 id="form-title" className="font-display text-[1.9rem] text-ink">Send a message</h2>
          <div className="mt-6 rounded-sm border border-rule bg-surface p-6">
            <Suspense fallback={null}>
              <EnquiryForm />
            </Suspense>
          </div>
        </section>
      </Container>
    </>
  );
}
