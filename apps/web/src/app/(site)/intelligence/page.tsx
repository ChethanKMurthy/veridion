import type { Metadata } from "next";
import Link from "next/link";
import { Container, CtaBand, Masthead } from "@/components/site/chrome";
import { BenchmarkPreview } from "@/components/site/previews";
import { ArrowRight } from "@/components/ui/icons";
import { num, signedPct, unit } from "@/lib/format";
import { highlights } from "@/lib/highlights";

export const metadata: Metadata = {
  title: "Company and peer intelligence",
  description:
    "Understand a company's disclosures over time and against its peers, with units aligned, periods checked and every number linked to its page.",
};

const checks = [
  ["Units", "Values are converted to a common unit before they are compared — GJ to MWh, ktCO₂e to tCO₂e, megalitres to cubic metres — and the conversion is shown."],
  ["Reporting periods", "Each company's financial year is respected. A year ending in March is flagged when it is compared with a calendar year."],
  ["Consolidation", "Operational control, financial control and equity share produce different totals. Where companies differ, the comparison says so."],
  ["Scope 2 method", "Location-based and market-based figures are kept apart. A figure without a stated method is labelled as such."],
  ["Source quality", "Values read from scanned pages carry their OCR confidence. Conflicting figures within a company's own documents are flagged."],
  ["Missing values", "A metric a company did not disclose is shown as not disclosed. It is never treated as zero, and never as poor performance."],
];

export default function IntelligencePage() {
  const h = highlights;
  return (
    <>
      <Masthead
        title="Know what changed, and how a company compares."
        lead="Veridion turns every disclosed figure into a typed value with its unit, period and source. That makes change over time and comparison between companies possible — with the limits stated beside each number."
      />

      <section className="bg-canvas">
        <Container className="grid gap-12 py-16 lg:grid-cols-[minmax(0,0.8fr)_minmax(0,1.2fr)] lg:py-24">
          <div>
            <h2 className="font-display text-[clamp(1.9rem,3.2vw,2.7rem)] leading-[1.1] tracking-[-0.01em] text-ink">Company intelligence</h2>
            <p className="mt-5 text-body text-ink-muted">
              Each company has a view of its key disclosures for the latest period, the prior period where it was reported, the
              change between them, and the page each figure came from. Unresolved questions — conflicts and findings that need a
              reviewer — sit beside them.
            </p>
            <p className="mt-4 text-body text-ink-muted">
              Change is shown without a judgement colour: lower emissions are usually good news, lower revenue usually is not.
            </p>
          </div>
          {h.key_disclosures?.length ? (
            <figure className="overflow-x-auto rounded-sm border border-rule bg-surface">
              <figcaption className="border-b border-rule px-5 py-3">
                <p className="text-ui font-medium text-ink">{h.company.name} · key disclosures</p>
                <p className="text-meta text-ink-muted">Fictional company · values recorded from the Veridion engine</p>
              </figcaption>
              <table className="w-full min-w-[520px] text-left text-ui-sm">
                <thead>
                  <tr className="border-b border-rule text-meta text-ink-muted">
                    <th className="px-5 py-2 font-medium">Metric</th>
                    <th className="px-3 py-2 text-right font-medium">FY2025</th>
                    <th className="px-3 py-2 text-right font-medium">Change</th>
                    <th className="px-5 py-2 font-medium">Source</th>
                  </tr>
                </thead>
                <tbody>
                  {h.key_disclosures.map((k) => (
                    <tr key={k.metric_key} className="border-b border-rule last:border-0">
                      <td className="px-5 py-2.5 text-ink">{k.label}</td>
                      <td className="tnum px-3 py-2.5 text-right text-ink">
                        {num(k.current.value)} <span className="text-ink-muted">{unit(k.current.unit)}</span>
                      </td>
                      <td className="tnum px-3 py-2.5 text-right text-ink-muted">{k.change === null ? "—" : signedPct(k.change)}</td>
                      <td className="px-5 py-2.5 text-meta text-ink-muted">{k.current.source}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </figure>
          ) : null}
        </Container>
      </section>

      <section className="border-t border-rule bg-surface">
        <Container className="py-16 lg:py-24">
          <h2 className="max-w-3xl font-display text-[clamp(1.9rem,3.2vw,2.7rem)] leading-[1.1] tracking-[-0.01em] text-ink">
            Peer comparisons that state their limits.
          </h2>
          <div className="mt-12 grid gap-12 lg:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
            <div className="space-y-6">
              <BenchmarkPreview metric="ghg_scope1" />
              <BenchmarkPreview metric="energy_total" />
            </div>
            <dl className="divide-y divide-rule self-start border-y border-rule">
              {checks.map(([k, v]) => (
                <div key={k} className="py-4">
                  <dt className="text-ui font-medium text-ink">{k}</dt>
                  <dd className="mt-1 text-ui text-ink-muted">{v}</dd>
                </div>
              ))}
            </dl>
          </div>
        </Container>
      </section>

      <section className="border-t border-rule bg-canvas">
        <Container className="grid gap-10 py-16 lg:grid-cols-2 lg:py-24">
          <div>
            <h2 className="font-display text-[clamp(1.9rem,3.2vw,2.7rem)] leading-[1.1] tracking-[-0.01em] text-ink">Value-chain coverage</h2>
            <p className="mt-5 text-body text-ink-muted">
              Coverage is part of the comparison. In the demo, one peer quantifies Scope 3 emissions while the focal company has
              only screened its categories — so the comparison shows a disclosure gap, not a performance gap.
            </p>
            <Link href={`/demo/companies/${h.company.id}/peers`} className="mt-7 inline-flex items-center gap-2 text-[0.95rem] font-medium text-ink underline decoration-rule-strong underline-offset-4 hover:decoration-ink">
              Open the peer view in the demo <ArrowRight size={16} />
            </Link>
          </div>
          <BenchmarkPreview metric="ghg_scope3" />
        </Container>
      </section>

      <CtaBand title="Compare the fictional peer group yourself." primary={{ href: `/demo/companies/${h.company.id}/peers`, label: "Open peer intelligence" }} />
    </>
  );
}
