import type { Metadata } from "next";
import Link from "next/link";
import { Container, CtaBand, Masthead } from "@/components/site/chrome";
import { PageCrop } from "@/components/site/page-crop";
import { ExplorerPreview } from "@/components/site/previews";
import { ArrowRight } from "@/components/ui/icons";
import { StatusLabel } from "@/components/ui/status";
import { num, pct, unit } from "@/lib/format";
import { highlights } from "@/lib/highlights";

export const metadata: Metadata = {
  title: "Evidence Explorer",
  description:
    "Every requirement, its status and the evidence behind it. Follow any finding through requirement, evidence, rationale, gap and action to the exact source passage.",
};

const columns = [
  ["Requirement", "The disclosure being assessed, from a versioned catalogue."],
  ["Status", "Supported, partially supported, evidence not found, conflicting, or human review required — each with its own shape."],
  ["Evidence coverage", "How much of the requirement's weighted elements are evidenced, segment by segment."],
  ["Primary source", "The document and page of the strongest supporting or conflicting passage."],
  ["Period", "The reporting period the evidence refers to, aligned to the company's financial year."],
  ["Assessed", "When the run finished and whether it used rules only or rules plus a model."],
  ["Review", "Whether a person has accepted or overridden the finding, or whether one should."],
];

export default function EvidenceExplorerPage() {
  const h = highlights;
  const c = h.conflict;
  return (
    <>
      <Masthead
        title="The Evidence Explorer"
        lead="Every requirement, its status and the evidence behind it. Select a finding and Veridion lays out the trail that produced it — and opens the exact passage on the page."
      >
        <Link
          href={c ? `/demo/companies/${h.company.id}/evidence?finding=${c.finding_id}` : "/demo"}
          className="inline-flex h-12 items-center gap-2 rounded-sm bg-on-dark px-5 text-[0.95rem] font-medium text-obsidian hover:bg-white"
        >
          Open it in the demo <ArrowRight size={16} />
        </Link>
      </Masthead>

      <section className="bg-canvas">
        <Container className="py-16 lg:py-24">
          <ExplorerPreview rows={9} className="border-rule shadow-none" />
          <p className="mt-3 text-meta text-ink-muted">
            {h.company.name} (fictional) assessed against {h.run.requirement_set_id}. Recorded from the Veridion engine.
          </p>
        </Container>
      </section>

      {c && c.low && c.high ? (
        <section className="border-t border-rule bg-surface">
          <Container className="py-16 lg:py-24">
            <h2 className="max-w-3xl font-display text-[clamp(1.9rem,3.2vw,2.7rem)] leading-[1.1] tracking-[-0.01em] text-ink">
              Read a finding the way an analyst would.
            </h2>
            <p className="mt-5 max-w-2xl text-body text-ink-muted">
              The trail for {c.display_code}, {c.title.toLowerCase()}, exactly as the demo shows it.
            </p>
            <ol className="mt-12 space-y-0">
              {[
                {
                  title: "Requirement",
                  body: (
                    <p className="text-ui text-ink-muted">
                      <span className="font-mono text-ink">{c.display_code}</span> · {c.title}. Elements: total energy consumption,
                      fuel by source, electricity, the reporting period, and the source of conversion factors.
                    </p>
                  ),
                },
                {
                  title: "Evidence",
                  body: (
                    <div className="grid gap-4 md:grid-cols-2">
                      {[c.low, c.high].map((crop, i) => (
                        <figure key={crop.id} className="overflow-hidden rounded-sm border border-rule">
                          <PageCrop src={crop.src} size={crop.size} bbox={crop.bbox} role={i === 0 ? "supporting" : "conflicting"} padY={34} padX={20} alt={`${crop.title}, page ${crop.page}: ${crop.text}`} />
                          <figcaption className="bg-canvas px-3 py-2 text-ui-sm text-ink">
                            {crop.document}, p.{crop.page}
                          </figcaption>
                        </figure>
                      ))}
                    </div>
                  ),
                },
                {
                  title: "Rationale",
                  body: <p className="text-ui leading-relaxed text-ink">{c.rationale.replace(/\s*\[?\(?ev_[0-9a-f]{20}\)?\]?/g, "")}</p>,
                },
                {
                  title: "Gap",
                  body: (
                    <p className="flex flex-wrap items-center gap-2 text-ui text-ink">
                      <StatusLabel status="conflicting" />
                      <span className="tnum text-ink-muted">
                        {num(c.conflict.low.value)} {unit(c.conflict.low.unit)} vs {num(c.conflict.high.value)}{" "}
                        {unit(c.conflict.high.unit)} (= {num(c.conflict.high.normalized_value)} {unit(c.conflict.high.normalized_unit)}) ·{" "}
                        {pct(c.conflict.relative_difference, 1)} apart, above the 1% tolerance
                      </span>
                    </p>
                  ),
                },
                {
                  title: "Action",
                  body: c.action ? (
                    <p className="text-ui text-ink">
                      {c.action.title} <span className="tnum text-ink-muted">· priority {c.action.priority_score.toFixed(2)} · {c.action.effort} effort</span>
                    </p>
                  ) : null,
                },
              ].map((step, i, all) => (
                <li key={step.title} className="relative grid grid-cols-[2.25rem_1fr] gap-x-4">
                  <div className="relative flex justify-center">
                    <span className="tnum relative z-[1] inline-flex size-8 items-center justify-center rounded-full border border-ink bg-surface text-ui-sm">{i + 1}</span>
                    {i < all.length - 1 ? <span className="absolute bottom-0 top-8 w-px bg-rule-strong" aria-hidden="true" /> : null}
                  </div>
                  <div className="pb-10">
                    <h3 className="pt-1 text-[1.05rem] font-semibold text-ink">{step.title}</h3>
                    <div className="mt-3">{step.body}</div>
                  </div>
                </li>
              ))}
            </ol>
          </Container>
        </section>
      ) : null}

      <section className="border-t border-rule bg-canvas">
        <Container className="grid gap-12 py-16 lg:grid-cols-2 lg:py-24">
          <div>
            <h2 className="font-display text-[clamp(1.9rem,3.2vw,2.7rem)] leading-[1.1] tracking-[-0.01em] text-ink">What each column tells you</h2>
            <dl className="mt-8 divide-y divide-rule border-y border-rule">
              {columns.map(([k, v]) => (
                <div key={k} className="grid gap-1 py-3 sm:grid-cols-[10rem_1fr] sm:gap-6">
                  <dt className="text-ui font-medium text-ink">{k}</dt>
                  <dd className="text-ui text-ink-muted">{v}</dd>
                </div>
              ))}
            </dl>
          </div>
          <div className="space-y-10">
            <div>
              <h2 className="font-display text-[1.8rem] leading-tight text-ink">Built for the keyboard</h2>
              <p className="mt-3 text-body text-ink-muted">
                Move through requirements with <kbd className="rounded-[2px] border border-rule-strong bg-surface px-1.5 font-mono text-[0.8rem]">↑</kbd>{" "}
                <kbd className="rounded-[2px] border border-rule-strong bg-surface px-1.5 font-mono text-[0.8rem]">↓</kbd>, open a trail with{" "}
                <kbd className="rounded-[2px] border border-rule-strong bg-surface px-1.5 font-mono text-[0.8rem]">Enter</kbd> and close it with{" "}
                <kbd className="rounded-[2px] border border-rule-strong bg-surface px-1.5 font-mono text-[0.8rem]">Esc</kbd>. Citations in the
                rationale jump to the passage they cite.
              </p>
            </div>
            <div>
              <h2 className="font-display text-[1.8rem] leading-tight text-ink">Reviews sit beside the assessment</h2>
              <p className="mt-3 text-body text-ink-muted">
                Accept a finding, override its status with a recorded reason, or comment. The original assessment is never
                overwritten, so a later reader can see both what the system concluded and what a person decided.
              </p>
            </div>
            <div>
              <h2 className="font-display text-[1.8rem] leading-tight text-ink">History is part of the record</h2>
              <p className="mt-3 text-body text-ink-muted">
                Compare any two runs to see which findings changed and why — a revised requirement, a replaced document or a
                different method.{h.diff ? ` In the demo: ${h.diff.summary}.` : ""}
              </p>
            </div>
          </div>
        </Container>
      </section>

      <CtaBand title="Follow a finding to its page." primary={{ href: c ? `/demo/companies/${h.company.id}/evidence?finding=${c.finding_id}` : "/demo", label: "Open the Evidence Explorer" }} />
    </>
  );
}
