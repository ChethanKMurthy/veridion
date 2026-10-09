import type { Metadata } from "next";
import Link from "next/link";
import { Container, CtaBand, Masthead } from "@/components/site/chrome";
import { ArrowRight } from "@/components/ui/icons";

export const metadata: Metadata = {
  title: "About",
  description: "Why Veridion exists, the principles it is built on, and where the company is today.",
};

const principles = [
  ["Every conclusion is one click from its source.", "If a finding, number or chart cannot be traced to a page and a passage, it does not ship."],
  ["Absence of evidence is not proof of non-compliance.", "Our language, statuses and reports keep what the documents establish separate from what a company does."],
  ["Uncertainty is shown, not hidden.", "Confidence, weak evidence, model disagreement and the limits of a comparison are part of the result."],
  ["Precision over decoration.", "We would rather show one number that holds up than ten that look impressive."],
  ["Honest about maturity.", "We describe only what is built, name no customers we do not have, and claim no certification we have not earned."],
];

export default function AboutPage() {
  return (
    <>
      <Masthead
        title="A private research institution, translated into software."
        lead="Veridion helps the people who review company disclosures reach conclusions they can defend — by connecting every claim to its evidence, and saying plainly where the evidence runs out."
      />

      <section className="bg-canvas">
        <Container className="grid gap-12 py-16 lg:grid-cols-[minmax(0,0.8fr)_minmax(0,1.2fr)] lg:py-24">
          <h2 className="font-display text-[clamp(1.9rem,3.2vw,2.7rem)] leading-[1.1] tracking-[-0.01em] text-ink">Why we are building it</h2>
          <div className="space-y-5 text-body text-ink-muted">
            <p>
              Company disclosures are long, scattered across reports and reporting periods, and written for many audiences at once.
              The people who review them — sustainability and compliance consultants, analysts, reporting teams — spend much of their
              time not judging the evidence but finding it, converting it and checking it against itself.
            </p>
            <p>
              General-purpose AI tools can summarise a report, but a summary is not a finding. A reviewer needs to know which
              requirement a passage addresses, whether it addresses all of it, whether another document says something different, and
              what to do about the gap — and they need to be able to show their working.
            </p>
            <p>
              Veridion is built around that need: a record that links each requirement, through its evidence and the reasoning
              applied to it, to the action it calls for. The software does the finding, converting and cross-checking. People make the
              judgements, and the record shows both.
            </p>
          </div>
        </Container>
      </section>

      <section className="border-t border-rule bg-surface">
        <Container className="py-16 lg:py-24">
          <h2 className="font-display text-[clamp(1.9rem,3.2vw,2.7rem)] leading-[1.1] tracking-[-0.01em] text-ink">Operating principles</h2>
          <dl className="mt-10 divide-y divide-rule border-y border-rule">
            {principles.map(([t, d]) => (
              <div key={t} className="grid gap-2 py-5 md:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)] md:gap-10">
                <dt className="font-serif text-[1.15rem] leading-snug text-ink">{t}</dt>
                <dd className="text-ui leading-relaxed text-ink-muted">{d}</dd>
              </div>
            ))}
          </dl>
        </Container>
      </section>

      <section className="on-dark bg-graphite text-on-dark">
        <Container className="grid gap-12 py-16 lg:grid-cols-2 lg:py-24">
          <div>
            <h2 className="font-display text-[clamp(1.9rem,3.2vw,2.7rem)] leading-[1.1] tracking-[-0.01em]">Where we are today</h2>
            <p className="mt-5 text-body text-on-dark-muted">
              Veridion is an early-stage product in development. The platform you can explore in the demo is working software: it
              ingests real PDFs, assesses them against a versioned catalogue and records every step. Its scope is deliberately
              narrow — climate and energy disclosures under the GRI Standards — so that it can be made reliable before it is made
              broad.
            </p>
            <p className="mt-4 text-body text-on-dark-muted">
              We are looking for a small number of sustainability and compliance consultants to pilot the workflow on their own
              material, and to tell us where it saves time and where it falls short.
            </p>
          </div>
          <div className="space-y-6 lg:pt-2">
            <div className="border-t border-rule-dark pt-5">
              <p className="text-[1.05rem] font-medium">No customer logos, no borrowed credibility</p>
              <p className="mt-2 text-ui text-on-dark-muted">We will name customers and partners only when they have agreed to be named.</p>
            </div>
            <div className="border-t border-rule-dark pt-5">
              <p className="text-[1.05rem] font-medium">Corporate details, when they exist</p>
              <p className="mt-2 text-ui text-on-dark-muted">
                Registration details will be published on the{" "}
                <Link href="/company/corporate-information" className="text-on-dark underline decoration-rule-dark-strong underline-offset-4">
                  corporate information
                </Link>{" "}
                page once the operating entity is established.
              </p>
            </div>
            <div className="border-t border-rule-dark pt-5">
              <Link href="/request-access" className="inline-flex items-center gap-2 text-[1.05rem] font-medium text-on-dark underline decoration-rule-dark-strong underline-offset-4 hover:decoration-on-dark">
                Become a pilot user <ArrowRight size={16} />
              </Link>
            </div>
          </div>
        </Container>
      </section>

      <CtaBand title="See the product we are building." />
    </>
  );
}
