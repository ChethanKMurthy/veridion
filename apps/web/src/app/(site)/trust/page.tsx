import type { Metadata } from "next";
import Link from "next/link";
import { Container, Masthead } from "@/components/site/chrome";
import { ArrowRight } from "@/components/ui/icons";

export const metadata: Metadata = {
  title: "Trust",
  description: "How Veridion handles security, data, and the use of AI — described as built, not as aspired to.",
};

const pages = [
  ["/trust/security", "Security", "Authentication, sessions, workspace isolation, uploads, audit logging, and how to report a vulnerability."],
  ["/trust/privacy", "Data handling", "What data Veridion processes, where it goes, how long it is kept, and what is never done with it."],
  ["/trust/ai-governance", "AI governance", "What the language model is allowed to do, what it is not, how its output is checked, and its known failure modes."],
  ["/trust/subprocessors", "Subprocessors", "External services that may process customer data, and when."],
  ["/legal/privacy-notice", "Privacy notice", "The plain-language privacy notice for this website and the platform."],
  ["/legal/accessibility", "Accessibility", "Our accessibility target, known issues and how to report a problem."],
];

export default function TrustPage() {
  return (
    <>
      <Masthead
        title="Trust is a description, not a badge."
        lead="Customers upload internal documents to Veridion, so how it handles them should be easy to find and easy to verify. These pages describe the system as it is built today, including what is not yet in place."
      />
      <Container className="py-16 lg:py-24">
        <ul className="divide-y divide-rule border-y border-rule">
          {pages.map(([href, title, body]) => (
            <li key={href}>
              <Link href={href} className="group grid gap-2 py-6 md:grid-cols-[16rem_minmax(0,1fr)_auto] md:items-baseline md:gap-8">
                <span className="font-display text-[1.6rem] leading-tight text-ink">{title}</span>
                <span className="text-ui text-ink-muted">{body}</span>
                <ArrowRight className="hidden text-ink-muted transition-transform group-hover:translate-x-0.5 md:block" />
              </Link>
            </li>
          ))}
        </ul>
        <div className="mt-14 max-w-3xl">
          <h2 className="font-display text-[1.9rem] text-ink">What we do not claim</h2>
          <p className="mt-3 text-body text-ink-muted">
            Veridion does not hold SOC 2, ISO 27001 or any other certification, and makes no claim of regulatory compliance on its own
            behalf. We will list certifications and audits here only after they have been completed. A small system described
            accurately is more useful to you than a page of badges.
          </p>
        </div>
      </Container>
    </>
  );
}
