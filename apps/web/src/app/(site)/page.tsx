import type { Metadata } from "next";
import Link from "next/link";
import { Container, CtaBand } from "@/components/site/chrome";
import { EvidenceInstrument } from "@/components/site/evidence-instrument";
import { BenchmarkPreview, ConflictPreview, ExplorerPreview, StatusLegend } from "@/components/site/previews";
import { ArrowRight } from "@/components/ui/icons";
import { StatusGlyph } from "@/components/ui/status";
import { num, pct, unit } from "@/lib/format";
import { highlights } from "@/lib/highlights";

export const metadata: Metadata = {
  title: { absolute: "Veridion — See what the evidence reveals" },
};

const steps = [
  {
    title: "Documents",
    body: "Every passage, table row and value keeps its page and position. Scanned pages are read with OCR and marked as such.",
    detail: "ev_93a18ca5… · p.4 · table row",
  },
  {
    title: "Evidence",
    body: "Values are extracted with their units and periods, normalised, and checked against each other across documents.",
    detail: "1,532,000 GJ → 425,556 MWh",
  },
  {
    title: "Assessment",
    body: "Each requirement in a versioned catalogue is checked element by element. A model can review the wording, but it can only cite passages that exist.",
    detail: "supported · partial · not found · conflicting · review",
  },
  {
    title: "Action",
    body: "Gaps become prioritised actions with owners and dates, kept across runs until the evidence closes them.",
    detail: "P = importance × gap × urgency",
  },
];

export default function HomePage() {
  const h = highlights;
  const conflict = h.conflict?.conflict;
  const scope1 = h.findings.find((f) => f.display_code.endsWith("305-1"));
  return (
    <>
      {/* Hero */}
      <section className="on-dark grain relative overflow-hidden bg-obsidian text-on-dark">
        <Container className="grid items-center gap-14 pb-20 pt-14 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.05fr)] lg:gap-10 lg:pb-28 lg:pt-24">
          <div className="max-w-xl">
            <h1 className="font-display text-[clamp(3rem,7vw,5.6rem)] leading-[0.98] tracking-[-0.02em]">
              See what the evidence reveals.
            </h1>
            <p className="mt-7 max-w-lg text-lead text-on-dark-muted">
              Turn company disclosures into traceable intelligence. Investigate claims, evaluate evidence, identify gaps, and
              understand how organizations compare.
            </p>
            <div className="mt-9 flex flex-wrap gap-3">
              <Link
                href="/demo"
                className="inline-flex h-12 items-center gap-2 rounded-sm bg-on-dark px-5 text-[0.95rem] font-medium text-obsidian transition-colors hover:bg-white"
              >
                Explore the platform <ArrowRight size={16} />
              </Link>
              <Link
                href="/methodology"
                className="inline-flex h-12 items-center rounded-sm border border-rule-dark-strong px-5 text-[0.95rem] text-on-dark transition-colors hover:border-on-dark-muted"
              >
                View the methodology
              </Link>
            </div>
            <p className="mt-5 text-ui-sm text-on-dark-muted">Interactive demo with fictional companies. No sign-up.</p>
          </div>
          <div className="lg:pl-6">
            <EvidenceInstrument
              low={conflict ? `${num(conflict.low.value)} ${unit(conflict.low.unit)}` : undefined}
              high={conflict ? `${num(conflict.high.value)} ${unit(conflict.high.unit)}` : undefined}
              converted={conflict ? `= ${num(conflict.high.normalized_value)} ${unit(conflict.high.normalized_unit)}` : undefined}
              difference={conflict ? pct(conflict.relative_difference, 1) : undefined}
              code={h.conflict?.display_code}
            />
          </div>
        </Container>
      </section>

      {/* The problem */}
      <section className="bg-canvas">
        <Container className="grid gap-12 py-20 lg:grid-cols-[minmax(0,0.85fr)_minmax(0,1.15fr)] lg:py-28">
          <div>
            <h2 className="font-display text-[clamp(2rem,3.6vw,3rem)] leading-[1.08] tracking-[-0.01em] text-ink">
              The answer is usually in the documents. Just not in one place.
            </h2>
            <p className="mt-6 text-body text-ink-muted">
              One disclosure question can span an annual report, a sustainability report, a policy and last year&apos;s figures —
              each with its own units, reporting period and boundary. Reviewers reconcile them by hand.
            </p>
            <p className="mt-4 text-body text-ink-muted">
              The gaps they find are easy to overstate. A figure missing from the documents provided is not the same as a company
              failing to comply.
            </p>
            <dl className="mt-8 space-y-3 border-t border-rule pt-6 text-ui">
              <div className="flex gap-3">
                <dt className="w-24 shrink-0 font-medium text-ink">Units</dt>
                <dd className="text-ink-muted">GJ against MWh, ktCO₂e against tCO₂e.</dd>
              </div>
              <div className="flex gap-3">
                <dt className="w-24 shrink-0 font-medium text-ink">Periods</dt>
                <dd className="text-ink-muted">A March year-end is not a calendar year.</dd>
              </div>
              <div className="flex gap-3">
                <dt className="w-24 shrink-0 font-medium text-ink">Boundaries</dt>
                <dd className="text-ink-muted">Operational control is not financial control.</dd>
              </div>
            </dl>
          </div>
          <div className="lg:pt-2">
            <ConflictPreview />
            {conflict ? (
              <p className="mt-4 text-ui-sm text-ink-muted">
                <StatusGlyph status="conflicting" className="mr-1.5 inline align-[-1px]" />
                Two reports from the same fictional company give total energy use {pct(conflict.relative_difference, 1)} apart once
                converted to the same unit. Veridion found both, converted them and flagged the conflict for a reviewer.
              </p>
            ) : null}
          </div>
        </Container>
      </section>

      {/* The method */}
      <section className="border-y border-rule bg-surface">
        <Container className="py-20 lg:py-28">
          <h2 className="max-w-3xl font-display text-[clamp(2rem,3.6vw,3rem)] leading-[1.08] tracking-[-0.01em] text-ink">
            From documents to decisions, one traceable step at a time.
          </h2>
          <ol className="mt-14 grid gap-10 md:grid-cols-2 lg:grid-cols-4 lg:gap-0">
            {steps.map((s, i) => (
              <li key={s.title} className="relative lg:pr-8">
                <div className="flex items-center gap-3">
                  <span className="tnum inline-flex size-8 shrink-0 items-center justify-center rounded-full border border-ink text-ui-sm">{i + 1}</span>
                  {i < steps.length - 1 ? <span className="hidden h-px flex-1 bg-rule-strong lg:block" aria-hidden="true" /> : null}
                </div>
                <h3 className="mt-5 text-[1.05rem] font-semibold text-ink">{s.title}</h3>
                <p className="mt-2 text-ui leading-relaxed text-ink-muted">{s.body}</p>
                <p className="mt-4 font-mono text-[0.72rem] text-ink-muted">{s.detail}</p>
              </li>
            ))}
          </ol>
        </Container>
      </section>

      {/* The platform */}
      <section className="on-dark bg-obsidian text-on-dark">
        <Container className="grid gap-12 py-20 lg:grid-cols-[minmax(0,0.75fr)_minmax(0,1.25fr)] lg:items-center lg:py-28">
          <div>
            <h2 className="font-display text-[clamp(2rem,3.6vw,3rem)] leading-[1.08] tracking-[-0.01em]">The Evidence Explorer</h2>
            <p className="mt-6 text-body text-on-dark-muted">
              Every requirement, its status and the evidence behind it. Select a finding to follow its trail — requirement,
              evidence, rationale, gap, action — and open the exact passage on the page it came from.
            </p>
            <p className="mt-4 text-body text-on-dark-muted">
              Reviewers accept or override findings with a recorded reason. The original assessment is never overwritten.
            </p>
            <Link
              href={h.conflict ? `/demo/companies/${h.company.id}/evidence?finding=${h.conflict.finding_id}` : "/demo"}
              className="mt-8 inline-flex items-center gap-2 text-[0.95rem] font-medium text-on-dark underline decoration-rule-dark-strong underline-offset-4 hover:decoration-on-dark"
            >
              Open the conflicting finding in the demo <ArrowRight size={16} />
            </Link>
          </div>
          <div>
            <ExplorerPreview />
            <p className="mt-3 text-meta text-on-dark-muted">
              Recorded from the Veridion engine ({h.run.mode === "hybrid" ? `rules + ${h.run.llm_model}` : "rules"}).{" "}
              {h.company.name} is a fictional company.
            </p>
          </div>
        </Container>
      </section>

      {/* Methodology */}
      <section className="bg-canvas">
        <Container className="grid gap-12 py-20 lg:grid-cols-2 lg:py-28">
          <div>
            <h2 className="font-display text-[clamp(2rem,3.6vw,3rem)] leading-[1.08] tracking-[-0.01em] text-ink">
              Absence of evidence is not evidence of non-compliance.
            </h2>
            <p className="mt-6 text-body text-ink-muted">
              Veridion reports what the documents establish, using five statuses with a distinct shape each. Anything it cannot
              resolve goes to a person, with the reason stated.
            </p>
            {scope1 ? (
              <div className="mt-8 rounded-sm border border-rule bg-surface p-5">
                <p className="text-ui-sm text-ink-muted">Every score is explained</p>
                <p className="mt-2 text-ui text-ink">
                  {scope1.display_code} {scope1.title}: <span className="tnum font-medium">{pct(scope1.completeness)}</span> of the
                  weighted elements are evidenced.
                  {scope1.missing_elements.length ? <> Missing: {scope1.missing_elements.map((m) => m.charAt(0).toLowerCase() + m.slice(1)).join("; ")}.</> : null}
                </p>
                <p className="mt-3 font-mono text-[0.75rem] text-ink-muted">completeness = Σ wᵢ·sᵢ / Σ wᵢ — an evidence measure, not a compliance score</p>
              </div>
            ) : null}
            <Link href="/methodology" className="mt-8 inline-flex items-center gap-2 text-[0.95rem] font-medium text-ink underline decoration-rule-strong underline-offset-4 hover:decoration-ink">
              Read the methodology <ArrowRight size={16} />
            </Link>
          </div>
          <StatusLegend className="self-start" />
        </Container>
      </section>

      {/* Intelligence */}
      <section className="border-y border-rule bg-surface">
        <Container className="grid gap-12 py-20 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)] lg:items-center lg:py-28">
          <BenchmarkPreview />
          <div className="lg:pl-6">
            <h2 className="font-display text-[clamp(2rem,3.6vw,3rem)] leading-[1.08] tracking-[-0.01em] text-ink">
              Compare like with like — or say why you can&apos;t.
            </h2>
            <p className="mt-6 text-body text-ink-muted">
              Peer figures are converted to the same unit before they are compared, and every comparison lists what limits it:
              different fiscal years, consolidation approaches, Scope 2 methods, or values read from a scanned page.
            </p>
            <p className="mt-4 text-body text-ink-muted">A value a company did not disclose is shown as not disclosed. Never as zero.</p>
            <Link href="/intelligence" className="mt-8 inline-flex items-center gap-2 text-[0.95rem] font-medium text-ink underline decoration-rule-strong underline-offset-4 hover:decoration-ink">
              How peer intelligence works <ArrowRight size={16} />
            </Link>
          </div>
        </Container>
      </section>

      {/* Trust */}
      <section className="on-dark bg-graphite text-on-dark">
        <Container className="py-20 lg:py-28">
          <h2 className="max-w-3xl font-display text-[clamp(2rem,3.6vw,3rem)] leading-[1.08] tracking-[-0.01em]">Built to be audited.</h2>
          <dl className="mt-12 grid gap-x-16 gap-y-10 md:grid-cols-2">
            {[
              ["Reproducible runs", "Each assessment records the hashes of the documents it read, the catalogue version, and the rule, prompt and model versions that produced it. Runs are never overwritten."],
              ["Versioned requirements", "Catalogues carry effective dates. GRI 302 and 305 (2016) apply to reports published before 1 January 2027; GRI 102 and 103 (2025) are available as a draft for early adopters."],
              ["A model that never acts", "When enabled, a language model reviews evidence and drafts rationale. It cannot change data, cannot override a detected conflict, and any citation it invents is discarded."],
              ["Isolated workspaces", "Every record belongs to one organization. Reviews, exports and plan changes are written to an append-only audit log."],
            ].map(([t, d]) => (
              <div key={t} className="border-t border-rule-dark pt-5">
                <dt className="text-[1.05rem] font-medium text-on-dark">{t}</dt>
                <dd className="mt-2 text-ui leading-relaxed text-on-dark-muted">{d}</dd>
              </div>
            ))}
          </dl>
          <p className="mt-12 text-ui text-on-dark-muted">
            We describe only what is built today.{" "}
            <Link href="/trust/security" className="font-medium text-on-dark underline decoration-rule-dark-strong underline-offset-4 hover:decoration-on-dark">
              Read how Veridion handles data
            </Link>
            .
          </p>
        </Container>
      </section>

      <CtaBand
        title="Inspect a finding yourself."
        body="The demo is a real Veridion workspace with fictional companies. Follow a finding to its page, compare a peer and act on a gap."
      />
    </>
  );
}
