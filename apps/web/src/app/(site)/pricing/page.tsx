import type { Metadata } from "next";
import Link from "next/link";
import { Container, CtaBand, Masthead } from "@/components/site/chrome";
import { cx } from "@/lib/format";
import { plans } from "@/lib/plans";

export const metadata: Metadata = {
  title: "Pricing",
  description: "Explorer, Professional and Enterprise plans for Veridion, with the usage limits each includes.",
};

const faq: [string, React.ReactNode][] = [
  [
    "Is there a free trial?",
    "Explorer workspaces have no charge during the pilot, within the limits shown. Professional pilots are arranged individually — request access and tell us what you would like to assess.",
  ],
  [
    "What counts as an assessment?",
    "One run of a requirement catalogue against a company's current documents for one reporting period. A model-assisted run also counts towards the model-assisted allowance. Viewing, reviewing and exporting existing runs never counts.",
  ],
  [
    "Are document uploads limited?",
    "Yes. Each plan includes a number of current documents and a maximum page count per document. Replaced versions do not count towards the document limit.",
  ],
  [
    "Which reporting frameworks are supported?",
    <>
      Today: a reviewed GRI 302 and 305 (2016) climate and energy catalogue, and a draft GRI 102 and 103 (2025) catalogue for early
      adoption. Other frameworks are not yet available; see the <Link href="/methodology#catalogues" className="underline underline-offset-2">methodology</Link> for how catalogues work.
    </>,
  ],
  ["Can I export reports?", "Yes, on every plan: a printable report, a CSV of findings, Markdown, and a JSON evidence package that records document hashes and engine versions."],
  [
    "Are API integrations available?",
    "The REST API that powers the interface is documented and available to every workspace, authenticated with a session token. Dedicated organization API keys and third-party integrations are not yet available.",
  ],
  ["Can multiple users collaborate?", "Yes, from Professional: owners, admins, analysts, reviewers and viewers, each with appropriate permissions. Explorer includes one seat."],
  [
    "Is customer data used to train models?",
    <>
      Veridion does not train models on customer documents. In model-assisted runs, the requirement text and up to twelve short passages per
      requirement are sent to the configured model provider for processing; rules-only runs send nothing externally. See{" "}
      <Link href="/trust/subprocessors" className="underline underline-offset-2">subprocessors</Link>.
    </>,
  ],
  [
    "What happens when a plan expires?",
    "Paid plans have not launched yet. Before they do, we will publish what happens to a workspace at the end of a subscription — including how to export everything first.",
  ],
  ["Can an organization request a pilot or custom agreement?", <>Yes. <Link href="/contact?topic=sales" className="underline underline-offset-2">Contact sales</Link> with your use case and expected volumes.</>],
];

export default function PricingPage() {
  return (
    <>
      <Masthead
        title="Plans for every stage of an evidence review."
        lead="Veridion is in its pilot phase. Explorer has no charge; Professional pilots are priced individually while we validate the offer with early users. Published prices will state the billing period, taxes, limits and cancellation terms."
      />
      <section className="bg-canvas">
        <Container className="py-16 lg:py-24">
          <div className="grid overflow-hidden rounded-sm border border-rule bg-surface lg:grid-cols-3">
            {plans.map((p, i) => (
              <div key={p.key} className={cx("flex flex-col p-7", i > 0 && "border-t border-rule lg:border-l lg:border-t-0")}>
                <h2 className="font-display text-[1.9rem] leading-none text-ink">{p.name}</h2>
                <p className="mt-3 min-h-12 text-ui text-ink-muted">{p.audience}</p>
                <p className="mt-6 text-[1.35rem] font-semibold text-ink">{p.price}</p>
                <p className="text-ui-sm text-ink-muted">{p.priceNote}</p>
                <Link
                  href={p.cta.href}
                  className={cx(
                    "mt-6 inline-flex h-11 items-center justify-center rounded-sm text-ui font-medium transition-colors",
                    p.key === "professional" ? "bg-obsidian text-on-dark hover:bg-graphite-2" : "border border-rule-strong text-ink hover:border-ink-muted",
                  )}
                >
                  {p.cta.label}
                </Link>
                <dl className="mt-8 divide-y divide-rule border-y border-rule text-ui-sm">
                  {p.limits.map(([k, v]) => (
                    <div key={k} className="flex justify-between gap-4 py-2">
                      <dt className="text-ink-muted">{k}</dt>
                      <dd className="tnum text-ink">{v}</dd>
                    </div>
                  ))}
                </dl>
                <ul className="mt-6 space-y-2 text-ui-sm text-ink">
                  {p.includes.map((x) => (
                    <li key={x} className="flex gap-2.5">
                      <span className="mt-2 size-1 shrink-0 rounded-full bg-ink" aria-hidden="true" />
                      {x}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
          <p className="mt-4 text-ui-sm text-ink-muted">
            Limits are enforced by the platform and shown in each workspace&apos;s settings. Enterprise limits are agreed in writing.
          </p>
        </Container>
      </section>

      <section className="border-t border-rule bg-surface">
        <Container className="grid gap-10 py-16 lg:grid-cols-[18rem_minmax(0,1fr)] lg:py-24">
          <h2 className="font-display text-[2.2rem] leading-tight text-ink">Questions</h2>
          <div className="divide-y divide-rule border-y border-rule">
            {faq.map(([q, a]) => (
              <details key={q} className="group py-5">
                <summary className="flex cursor-pointer list-none items-start justify-between gap-6 text-[1.02rem] font-medium text-ink [&::-webkit-details-marker]:hidden">
                  <span>{q}</span>
                  <span aria-hidden="true" className="mt-1 text-ink-muted transition-transform group-open:rotate-45">+</span>
                </summary>
                <div className="mt-3 max-w-3xl text-ui leading-relaxed text-ink-muted">{a}</div>
              </details>
            ))}
          </div>
        </Container>
      </section>
      <CtaBand title="Start with the demo, or start a pilot." primary={{ href: "/demo", label: "Explore the platform" }} secondary={{ href: "/request-access", label: "Request access" }} />
    </>
  );
}
