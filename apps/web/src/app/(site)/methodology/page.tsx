import type { Metadata } from "next";
import Link from "next/link";
import { Container, CtaBand, Masthead } from "@/components/site/chrome";
import { StatusLegend } from "@/components/site/previews";
import evaluation from "@/content/evaluation.json";
import { pct } from "@/lib/format";

export const metadata: Metadata = {
  title: "Methodology",
  description:
    "How Veridion extracts evidence, assesses requirements, uses a language model under constraint, prioritises gaps and measures its own accuracy — including where it can be wrong.",
};

type ModeMetrics = Record<string, number | null>;
type EvalRun = {
  generated_at: string;
  set_id: string;
  cases: number;
  corpus_cases: number;
  synthetic_cases: number;
  sampled: boolean;
  modes: Record<string, ModeMetrics>;
};
const ev = evaluation as unknown as {
  comparison: EvalRun;
  baseline_full: EvalRun;
  failures: { id: string; gold: string; predicted: string; mode: string }[];
};

const toc = [
  ["principles", "Principles"],
  ["ingestion", "Ingestion"],
  ["extraction", "Extraction"],
  ["retrieval", "Retrieval"],
  ["catalogues", "Requirement catalogues"],
  ["assessment", "Assessment and statuses"],
  ["model", "The model's role"],
  ["priority", "Prioritisation"],
  ["reproducibility", "Reproducibility"],
  ["evaluation", "Evaluation"],
  ["limitations", "Known limitations"],
];

const metricRows: [string, string, boolean][] = [
  ["status_accuracy", "Status accuracy (five statuses)", true],
  ["gap_precision", "Gap detection — precision", true],
  ["gap_recall", "Gap detection — recall", true],
  ["element_precision", "Element detection — precision", true],
  ["element_recall", "Element detection — recall", true],
  ["conflict_precision", "Contradiction detection — precision", true],
  ["conflict_recall", "Contradiction detection — recall", true],
  ["recall_at_5", "Retrieval Recall@5 (hand-labelled corpus)", true],
  ["support_precision", "Evidence-support precision (corpus)", true],
  ["numeric_accuracy", "Numeric extraction accuracy", true],
  ["citation_validity", "Citation validity", true],
  ["review_rate", "Human-review rate", true],
];

function H2({ id, children }: { id: string; children: React.ReactNode }) {
  return (
    <h2 id={id} className="scroll-mt-24 font-display text-[clamp(1.8rem,3vw,2.4rem)] leading-tight tracking-[-0.01em] text-ink">
      {children}
    </h2>
  );
}

export default function MethodologyPage() {
  const modes = Object.keys(ev.comparison.modes);
  const label: Record<string, string> = { rules: "Rules baseline", hybrid: "Rules + model" };
  return (
    <>
      <Masthead
        title="How Veridion reaches a conclusion — and where it can be wrong."
        lead="Every step below is implemented in the product today. Where a step has known weaknesses, they are listed at the end of the page."
      />
      <Container className="py-16 lg:py-24">
        <div className="grid gap-12 lg:grid-cols-[14rem_minmax(0,1fr)]">
          <nav aria-label="On this page" className="lg:sticky lg:top-24 lg:self-start">
            <p className="text-ui-sm font-medium text-ink">On this page</p>
            <ol className="mt-3 space-y-1.5 border-l border-rule pl-4 text-ui-sm">
              {toc.map(([id, l]) => (
                <li key={id}>
                  <a href={`#${id}`} className="text-ink-muted hover:text-ink">{l}</a>
                </li>
              ))}
            </ol>
          </nav>

          <div className="prose-veridion max-w-[72ch] [&>section]:mt-16 [&>section:first-child]:mt-0">
            <section>
              <H2 id="principles">Principles</H2>
              <ul>
                <li><strong>Evidence before conclusions.</strong> A finding exists only if it can point to passages on pages, or state precisely what was not found.</li>
                <li><strong>Absence is not non-compliance.</strong> Veridion assesses the documents it was given. A missing figure may exist elsewhere, or the requirement may not apply.</li>
                <li><strong>Deterministic first, model second.</strong> Numbers, units and periods are extracted and compared by code. A language model, when enabled, reviews wording — it does not decide figures.</li>
                <li><strong>Reproducible by design.</strong> Every run records its inputs and versions and is never overwritten.</li>
              </ul>
            </section>

            <section>
              <H2 id="ingestion">Ingestion</H2>
              <p>
                PDFs are parsed page by page. Text blocks become passages — paragraphs, headings and list items — with their page
                number and bounding box. Ruled tables are detected and each row becomes its own citeable passage, keeping the column
                headers so a value can be tied to its year. Headings build a section path, so a passage knows it sits under
                “Greenhouse gas emissions › Performance”.
              </p>
              <p>
                Pages without a text layer are rendered at 300 DPI and read with Tesseract OCR. Table rows on scanned pages are
                reconstructed from aligned text lines. Every OCR passage carries the engine&apos;s confidence, and a requirement that
                rests only on low-confidence OCR text is sent to human review.
              </p>
              <p>
                Running headers, footers and page numbers repeated across pages are removed. Each passage receives a stable evidence
                identifier derived from its document, page, position and text, so re-processing the same document version yields the
                same identifiers and earlier findings keep pointing at the right place.
              </p>
            </section>

            <section>
              <H2 id="extraction">Extraction</H2>
              <p>
                Values are paired with units and reporting periods before they are stored. Numbers are parsed with thousands
                separators, bracketed negatives and scale words (thousand, million, lakh, crore). Units are normalised within a
                family — emissions to tCO₂e, energy to MWh (1 MWh = 3.6 GJ), water to m³, waste to tonnes — and a value is only ever
                compared with values of the same family.
              </p>
              <p>
                Periods follow each company&apos;s financial year: FY2025 for a company with a March year end runs from 1 April 2024
                to 31 March 2025. Explicit dates (“year ended 31 December 2025”) take precedence; base-year statements (“in the 2019
                base year, emissions were…”) are dated to the base year; and a parenthetical such as “(2024: 50,115)” labels the
                value that follows it, not the one before.
              </p>
              <p>
                A value is assigned to a metric — Scope 1 emissions, location-based Scope 2, total energy — only when its unit
                family and the surrounding wording agree. When the extractor is unsure, it extracts nothing.
              </p>
            </section>

            <section>
              <H2 id="retrieval">Retrieval</H2>
              <p>
                For each requirement, passages are ranked by BM25 keyword relevance, exact phrase matches, whether the passage holds an
                extracted value for the requirement&apos;s metrics, and whether its section heading matches. Every result records why
                it matched, and the search screen shows that explanation. Semantic embeddings can be added behind the same interface;
                they will be added when the evaluation shows they improve recall.
              </p>
            </section>

            <section>
              <H2 id="catalogues">Requirement catalogues</H2>
              <p>
                Requirements live in versioned catalogue files. Each requirement is broken into weighted elements — for GRI 305-1,
                the gross value, its period, the consolidation approach, the methodology, gases, emission factors, base year and
                biogenic CO₂ — and each element has a defined evidence check: a typed value for the period, a stated period, wording,
                any of several checks, or a conditional check that applies only when triggered.
              </p>
              <p>
                Catalogues carry effective dates. The GRI 302 and 305 (2016) set applies to reports published before 1 January 2027,
                when GRI 102: Climate Change 2025 and GRI 103: Energy 2025 take effect. The 2025 set is published as a draft: its
                disclosure numbers and titles follow GRI, but its element definitions have not yet been verified against the full
                official text.
              </p>
              <p>
                Requirement summaries are Veridion&apos;s paraphrases, written for assessment. They are not the authoritative text of
                any standard. Once a catalogue version has been used in an assessment it cannot change; revisions are published as
                new versions with a changelog, and reviewers can record that a requirement does not apply to a company, with a
                rationale.
              </p>
            </section>

            <section>
              <H2 id="assessment">Assessment and statuses</H2>
              <p>
                Each element is checked against all current documents for the company. Completeness is the weighted share of
                applicable elements that are evidenced:
              </p>
              <blockquote>
                completeness = Σ wᵢ·sᵢ ÷ Σ wᵢ, where sᵢ is 1 when element i is evidenced and wᵢ is its catalogue weight.
              </blockquote>
              <p>
                It is an internal measure of evidence completeness, not a compliance score. Status then follows simple, published
                rules: conflicting when two sources disagree by more than 1% after unit conversion; supported when every applicable
                element is evidenced; partially supported when some are; evidence not found when none is.
              </p>
              <StatusLegend className="not-prose mt-6" />
            </section>

            <section>
              <H2 id="model">The model&apos;s role</H2>
              <p>
                In AI-assisted runs, a language model reviews each requirement. It receives the requirement, the result of every
                element check and at most twelve candidate passages, each truncated to 600 characters and labelled with its evidence
                identifier. It must answer in a strict JSON schema with a verdict for every element and the identifiers it relies on.
              </p>
              <ul>
                <li>Every cited identifier is checked against the candidates it was shown. Unknown identifiers are discarded and recorded.</li>
                <li>Numbers, units and periods are decided by the extraction rules. If the model disagrees, the finding is flagged for review rather than changed.</li>
                <li>Wording elements may be adjusted by the model — for example when a matched “baseline” belongs to a different target — and every adjustment is recorded on the finding.</li>
                <li>A detected conflict can never be overridden by the model.</li>
                <li>Passage text is treated as data, not instructions. The model has no tools and cannot write to the database.</li>
              </ul>
              <p>
                Calls use temperature zero, and responses are cached by model, prompt version and input, so re-running an assessment
                on unchanged inputs reproduces the result. Model mode can be switched off entirely; rules-only runs send nothing to any
                external service.
              </p>
            </section>

            <section>
              <H2 id="priority">Prioritisation</H2>
              <p>Gaps become actions ranked by a working heuristic, with every component visible:</p>
              <table>
                <thead>
                  <tr><th>Component</th><th>Meaning</th><th>Values</th></tr>
                </thead>
                <tbody>
                  <tr><td>I — importance</td><td>Catalogue importance of the requirement</td><td>0.4 · 0.7 · 1.0</td></tr>
                  <tr><td>G — gap</td><td>Size of the evidence gap</td><td>1 − completeness; 0.8 for conflicts; 1.0 when nothing is found</td></tr>
                  <tr><td>U — urgency</td><td>Time to the reporting deadline</td><td>1.0 within 30 days, 0.8 within 90, 0.6 within 180, 0.4 later; 0.5 with no deadline</td></tr>
                </tbody>
              </table>
              <p>P = I × G × U. It ranks work; it is not a regulatory formula.</p>
            </section>

            <section>
              <H2 id="reproducibility">Reproducibility</H2>
              <p>
                Assessment = f(documents, requirements, rules, model). Each run stores the SHA-256 hash and version of every document it
                read, the content hash of every requirement, and the pipeline, extraction, rules and prompt versions together with the
                model identifier and configuration. A new document version or catalogue revision produces a new run; the earlier run
                is kept. Comparing two runs attributes each change to a revised requirement, a replaced document or a different
                method, and findings that cite a since-replaced document are marked for reassessment.
              </p>
            </section>

            <section>
              <H2 id="evaluation">Evaluation</H2>
              <p>
                Veridion is measured on a labelled dataset of {ev.baseline_full.cases} cases: {ev.baseline_full.corpus_cases} hand-labelled
                requirement assessments on the fictional sample companies, and {ev.baseline_full.synthetic_cases} generated cases that mix
                standard wording, paraphrases written to evade keyword rules, absent elements, and traps — wording that looks relevant but
                does not satisfy the element.
              </p>
              <p>
                The table compares rules-only and rules + model ({ev.comparison.cases} cases: every hand-labelled case and an evenly spaced
                sample of the generated ones, run on {new Date(ev.comparison.generated_at).toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" })}).
                On the full set of {ev.baseline_full.cases} cases, the rules-only baseline reaches{" "}
                {pct(ev.baseline_full.modes.rules.status_accuracy as number, 1)} status accuracy and{" "}
                {pct(ev.baseline_full.modes.rules.gap_recall as number, 1)} gap recall.
              </p>
              <div className="not-prose mt-6 overflow-x-auto rounded-sm border border-rule bg-surface">
                <table className="w-full min-w-[420px] text-left text-ui-sm">
                  <thead>
                    <tr className="border-b border-rule text-meta text-ink-muted">
                      <th className="px-4 py-2.5 font-medium">Metric ({ev.comparison.cases} cases)</th>
                      {modes.map((m) => (
                        <th key={m} className="px-4 py-2.5 text-right font-medium">{label[m] ?? m}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {metricRows.map(([key, l]) => (
                      <tr key={key} className="border-b border-rule last:border-0">
                        <td className="px-4 py-2.5 text-ink">{l}</td>
                        {modes.map((m) => (
                          <td key={m} className="tnum px-4 py-2.5 text-right text-ink">
                            {ev.comparison.modes[m][key] === null || ev.comparison.modes[m][key] === undefined ? "—" : pct(ev.comparison.modes[m][key] as number, 1)}
                          </td>
                        ))}
                      </tr>
                    ))}
                    <tr className="border-t border-rule">
                      <td className="px-4 py-2.5 text-ink">Median time per requirement</td>
                      {modes.map((m) => (
                        <td key={m} className="tnum px-4 py-2.5 text-right text-ink">{Math.round(ev.comparison.modes[m].latency_ms as number).toLocaleString("en-GB")} ms</td>
                      ))}
                    </tr>
                    <tr>
                      <td className="px-4 py-2.5 text-ink">Model tokens per requirement</td>
                      {modes.map((m) => (
                        <td key={m} className="tnum px-4 py-2.5 text-right text-ink">{Math.round(ev.comparison.modes[m].tokens as number).toLocaleString("en-GB")}</td>
                      ))}
                    </tr>
                  </tbody>
                </table>
              </div>
              <h3>What the numbers say</h3>
              <p>
                The model&apos;s main contribution is recall on wording: it recognises elements written in ways the keyword rules miss,
                raising element recall without lowering contradiction detection, which stays with the deterministic checks. Overall
                status accuracy is the same in both modes on this sample, and the model sends more findings to human review.
              </p>
              <p>
                The model also makes its own mistakes. In this run it accepted a baseline that belonged to an emissions target as the
                baseline for energy savings, and it treated emissions figures as a description of the scopes in which reductions
                occurred. Both errors were recorded on the findings as model adjustments, so a reviewer can see and reverse them.
              </p>
              <p>
                The dataset is small and was authored by the people who built the system, so these figures describe behaviour on
                controlled cases. They are not a claim about accuracy on real-world reports, and they are not a comparison with other
                products. The full report, including every failure case, is published with the source code.
              </p>
            </section>

            <section>
              <H2 id="limitations">Known limitations</H2>
              <ul>
                <li>The requirement catalogue covers a focused climate and energy subset of the GRI Standards. Other frameworks are not yet modelled.</li>
                <li>Borderless tables in digital PDFs are read as text, which can miss values that a ruled table would capture.</li>
                <li>OCR on complex scanned layouts can misread figures. Such values are marked and lower the finding&apos;s confidence.</li>
                <li>Keyword rules miss some paraphrases and can be misled by wording that sounds right; the model review reduces but does not remove this.</li>
                <li>Documents are assumed to be in English.</li>
                <li>Model results can vary between providers and model versions. Each run records the model used.</li>
                <li>Applicability is assumed unless a reviewer records otherwise; Veridion does not determine materiality.</li>
              </ul>
              <p>
                Questions about the method are welcome — <Link href="/contact">contact us</Link>, or read how the model is governed on
                the <Link href="/trust/ai-governance">AI governance</Link> page.
              </p>
            </section>
          </div>
        </div>
      </Container>
      <CtaBand title="Test the method on a finding." body="Open a finding in the demo, follow its citations, and compare the rules and model views side by side." />
    </>
  );
}
