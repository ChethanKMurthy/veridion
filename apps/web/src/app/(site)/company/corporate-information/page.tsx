import type { Metadata } from "next";
import Link from "next/link";
import { Container, Masthead } from "@/components/site/chrome";
import { site } from "@/lib/site";

export const metadata: Metadata = {
  title: "Corporate information",
  description: "Legal entity, registration and official contact details for Veridion.",
};

function Row({ label, value }: { label: string; value: React.ReactNode | null }) {
  return (
    <div className="grid gap-1 py-4 sm:grid-cols-[16rem_1fr] sm:gap-8">
      <dt className="text-ui font-medium text-ink">{label}</dt>
      <dd className="text-ui text-ink-muted">{value ?? <span className="italic">Not yet established</span>}</dd>
    </div>
  );
}

export default function CorporateInformationPage() {
  const c = site.corporate;
  const m = site.mailboxes;
  const incorporated = c.status === "incorporated";
  return (
    <>
      <Masthead title="Corporate information" lead="The legal and official contact details for Veridion. Details appear here only once they are true." />
      <Container className="py-16 lg:py-24">
        {!incorporated ? (
          <div className="mb-12 max-w-3xl rounded-sm bg-brass-tint px-5 py-4 text-ui text-ink">
            Veridion is currently a product and venture in development and is not yet operating through an incorporated company.
            When the operating entity is established, its registered name, registration number and registered office will be
            published on this page. Until then, please use the <Link href="/contact" className="font-medium underline underline-offset-2">contact form</Link>{" "}
            for all enquiries.
          </div>
        ) : null}
        <div className="grid gap-12 lg:grid-cols-2">
          <section>
            <h2 className="font-display text-[1.9rem] text-ink">Legal entity</h2>
            <dl className="mt-6 divide-y divide-rule border-y border-rule">
              <Row label="Registered legal name" value={c.legalName} />
              <Row label="Entity type" value={c.entityType} />
              <Row label="Country of incorporation" value={c.countryOfIncorporation} />
              <Row label="Registration number" value={c.registrationNumber} />
              <Row label="Registered office" value={c.registeredOffice} />
              <Row label="Principal business address" value={c.principalBusinessAddress} />
              <Row label="Tax registrations" value={c.taxRegistrations.length ? c.taxRegistrations.join(", ") : null} />
              <Row
                label="Officers and representatives"
                value={c.officers.length ? c.officers.map((o) => `${o.name}, ${o.role}`).join("; ") : null}
              />
            </dl>
          </section>
          <section>
            <h2 className="font-display text-[1.9rem] text-ink">Corporate contact</h2>
            <dl className="mt-6 divide-y divide-rule border-y border-rule">
              {(
                [
                  ["General enquiries", m.general, "general"],
                  ["Business development", m.sales, "sales"],
                  ["Customer support", m.support, "support"],
                  ["Privacy enquiries", m.privacy, "privacy"],
                  ["Security reports", m.security, "security"],
                ] as const
              ).map(([label, mailbox, topic]) => (
                <Row
                  key={label}
                  label={label}
                  value={
                    mailbox ? (
                      <a href={`mailto:${mailbox}`} className="underline underline-offset-2">{mailbox}</a>
                    ) : (
                      <Link href={`/contact?topic=${topic}`} className="text-ink underline decoration-rule-strong underline-offset-2">
                        Use the contact form
                      </Link>
                    )
                  }
                />
              ))}
            </dl>
            <p className="mt-6 text-ui-sm text-ink-muted">
              Regulatory registrations, licences and certifications are listed here only when they are actually held. Veridion holds
              none at present.
            </p>
          </section>
        </div>
      </Container>
    </>
  );
}
