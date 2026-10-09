import type { ReactNode } from "react";

export type Article = {
  slug: string;
  title: string;
  summary: string;
  date: string;
  readingTime: string;
  topic: string;
  body: ReactNode;
  sources?: { label: string; url: string }[];
};

export const articles: Article[] = [
  {
    slug: "absence-of-evidence",
    title: "Absence of evidence is not evidence of non-compliance",
    summary:
      "Gap reports routinely turn “we could not find it” into “they do not do it”. Keeping three different situations apart makes a gap report more useful — and more defensible.",
    date: "2026-10-02",
    readingTime: "6 min read",
    topic: "Methodology",
    body: (
      <>
        <p>
          A gap analysis asks a simple-sounding question: does the evidence support this disclosure requirement? The answer is
          often recorded as a single word — compliant, non-compliant, partial — and that word travels into slide decks, board
          papers and client letters. The trouble is that “non-compliant” usually describes something narrower than it claims.
        </p>
        <h2>Three situations that look the same</h2>
        <p>When a reviewer cannot find evidence for a requirement, one of at least three things is true:</p>
        <ol>
          <li>
            <strong>The evidence exists, but was not found.</strong> It sits in a document nobody provided, in an appendix the search
            did not reach, or in wording that did not match the reviewer&apos;s expectations.
          </li>
          <li>
            <strong>The evidence does not exist in the documents provided.</strong> The disclosure is genuinely missing from the
            material under review — which is a gap in the documents, not yet a finding about the company.
          </li>
          <li>
            <strong>The requirement does not apply.</strong> Many disclosures depend on materiality, sector or circumstance. A
            market-based Scope 2 figure, for example, is only expected where an organization uses contractual instruments.
          </li>
        </ol>
        <p>
          Only after these are separated — and after someone with authority has considered the company&apos;s actual practices — can
          a statement about compliance be made. Collapsing them into one label overstates what the review established and invites
          the wrong remediation.
        </p>
        <h2>What a better status vocabulary looks like</h2>
        <p>
          Veridion reports what the documents establish, not what the company does. Its five statuses are deliberately narrow:
          supported, partially supported, evidence not found, conflicting evidence, and human review required. “Evidence not found”
          means exactly that, and every such finding says how many documents were assessed and that the evidence may exist
          elsewhere.
        </p>
        <p>
          Partial support is broken down further. Each requirement is split into elements — a value, its reporting period, the
          consolidation approach, the methodology — and the finding lists which are evidenced and which are missing. “Scope 1 is
          partially supported because biogenic CO₂ is not reported separately” is actionable; “Scope 1 is 92% compliant” is not, and
          it is not true either.
        </p>
        <h2>Conflicts deserve their own word</h2>
        <p>
          When two documents disagree — a sustainability report and an annual report stating different energy totals for the same
          year — the requirement is neither supported nor missing. It is conflicting, and the right next step is reconciliation, not
          data collection. In Veridion&apos;s demo, a fictional company reports 412,300 MWh in one document and 1,532,000 GJ (about
          425,556 MWh) in another. The difference only appears once units are aligned, and it is exactly the kind of inconsistency an
          auditor would ask about.
        </p>
        <h2>Write the uncertainty down</h2>
        <p>
          The final safeguard is a person. Findings that rest on low-confidence OCR text, where a language model and the
          deterministic checks disagree, or where values conflict, are routed to human review with the reason stated. Reviewers can
          accept or override a finding, but the original assessment is kept alongside the decision, so a later reader can see both.
        </p>
        <p>
          None of this makes a gap report more cautious for its own sake. It makes it more precise — and precision is what makes a
          finding defensible when a client, an auditor or a regulator asks how it was reached.
        </p>
      </>
    ),
  },
  {
    slug: "comparing-like-with-like",
    title: "Comparing emissions across fiscal years, units and boundaries",
    summary:
      "Two companies' Scope 1 figures can sit side by side in a table and still not be comparable. A short checklist for peer benchmarking that holds up.",
    date: "2026-09-24",
    readingTime: "7 min read",
    topic: "Peer intelligence",
    body: (
      <>
        <p>
          Peer benchmarking is one of the most requested outputs of a disclosure review and one of the easiest to get wrong. Each
          figure may be accurate and the comparison still mislead. Before putting two numbers next to each other, check six things.
        </p>
        <h2>1. Units</h2>
        <p>
          Emissions appear in tonnes, thousands of tonnes and kilograms of CO₂ equivalent; energy in megawatt-hours, gigajoules and
          gigawatt-hours. Convert to a single unit before comparing, and show the conversion. One megawatt-hour is 3.6 gigajoules —
          small conversion errors are a common source of apparent conflicts.
        </p>
        <h2>2. Reporting periods</h2>
        <p>
          A company with a financial year ending in March reports a period that overlaps two calendar years. Its “FY2025” runs from
          April 2024 to March 2025. Comparing it with a calendar-year company is often unavoidable, but the difference should be stated
          beside the figure rather than hidden.
        </p>
        <h2>3. Consolidation approach</h2>
        <p>
          The GHG Protocol allows emissions to be consolidated by operational control, financial control or equity share. The same
          group can report materially different totals under each. A benchmark should record each company&apos;s approach and flag
          differences.
        </p>
        <h2>4. Scope 2 method</h2>
        <p>
          Scope 2 emissions can be calculated on a location basis, using average grid factors, or on a market basis, reflecting
          contractual instruments such as power purchase agreements. A market-based figure is often much lower. Compare like with
          like, and label any figure whose method is not stated.
        </p>
        <h2>5. Source quality</h2>
        <p>
          A value read from a scanned appendix, or one that differs between a company&apos;s own documents, deserves a caveat. In
          Veridion, values read by OCR carry their confidence, and companies whose documents disagree are flagged in the benchmark.
        </p>
        <h2>6. Missing is not zero</h2>
        <p>
          The most damaging error is the quietest: treating an undisclosed metric as zero, or as poor performance. A company that has
          not quantified Scope 3 emissions has a disclosure gap, not small value-chain emissions. Show it as “not disclosed”.
        </p>
        <h2>Putting it into practice</h2>
        <p>
          In Veridion&apos;s peer view, every cell carries its value in a common unit, its period and its source page, followed by
          notes for each of the checks above that applies. The overall verdict for each metric — directly comparable, limited
          comparability, or insufficient disclosure — is stated in words, because a chart alone cannot carry the caveats.
        </p>
      </>
    ),
    sources: [{ label: "GHG Protocol Corporate Accounting and Reporting Standard", url: "https://ghgprotocol.org/corporate-standard" }],
  },
  {
    slug: "gri-102-103-2027",
    title: "GRI 102 and GRI 103 arrive in 2027: what changes for climate and energy disclosures",
    summary:
      "GRI's new Climate Change and Energy standards replace most of GRI 305 and all of GRI 302. A factual summary of what changes and when — and why requirement catalogues need effective dates.",
    date: "2026-09-10",
    readingTime: "6 min read",
    topic: "Standards",
    body: (
      <>
        <p>
          In June 2025 the Global Reporting Initiative published two new topic standards: GRI 102: Climate Change 2025 and GRI 103:
          Energy 2025. Both take effect on 1 January 2027. For organizations reporting on emissions and energy with reference to the
          GRI Standards, they change which disclosures apply — and they illustrate why a requirement checklist cannot be hard-coded.
        </p>
        <h2>What GRI 102 replaces</h2>
        <p>
          GRI 102 withdraws disclosures 305-1 to 305-5 of GRI 305: Emissions 2016 — direct, energy indirect and other indirect
          emissions, emissions intensity and emissions reductions — together with disclosure 201-2 of GRI 201 on climate-related
          financial implications. Disclosures 305-6 (ozone-depleting substances) and 305-7 (nitrogen oxides, sulphur oxides and other
          significant air emissions) remain in GRI 305.
        </p>
        <p>GRI 102 contains ten disclosures:</p>
        <table>
          <thead>
            <tr><th>Disclosure</th><th>Title</th></tr>
          </thead>
          <tbody>
            {[
              ["102-1", "Transition plan for climate change mitigation"],
              ["102-2", "Climate change adaptation plan"],
              ["102-3", "Just transition"],
              ["102-4", "GHG emissions reduction targets and progress"],
              ["102-5", "Scope 1 GHG emissions"],
              ["102-6", "Scope 2 GHG emissions"],
              ["102-7", "Scope 3 GHG emissions"],
              ["102-8", "GHG emissions intensity"],
              ["102-9", "GHG removals in the value chain"],
              ["102-10", "Carbon credits"],
            ].map(([d, t]) => (
              <tr key={d}><td>{d}</td><td>{t}</td></tr>
            ))}
          </tbody>
        </table>
        <p>
          The headline additions are transition and adaptation plans, just transition, and carbon credits, alongside a stronger
          focus on targets and on value-chain (Scope 3) emissions.
        </p>
        <h2>What GRI 103 replaces</h2>
        <p>
          GRI 103: Energy 2025 replaces GRI 302: Energy 2016 in full. It has five disclosures, 103-1 to 103-5, covering energy
          policies and commitments, energy consumption and generation within the organization, energy consumption in the value
          chain, energy intensity, and reductions in energy consumption. According to GRI&apos;s FAQ, it extends the requirements on
          purchased and self-generated electricity — including a breakdown by energy source and whether it is renewable — requires
          the numerator of the energy intensity ratio to be reported, and folds the former disclosure on reductions in the energy
          requirements of products and services into the reduction disclosure.
        </p>
        <h2>When it applies</h2>
        <p>
          GRI&apos;s FAQ for GRI 103 states that its use is required for all reporting on energy published on or after 1 January 2027,
          and that earlier adoption is encouraged; GRI 102 takes effect on the same date. Some commentators describe the trigger as
          reporting periods beginning on or after that date instead. The difference matters for a report covering 2026 but published
          in 2027, so confirm the trigger against the official text for each report.
        </p>
        <h2>The European picture</h2>
        <p>
          Separately, on 3 July 2026 the European Commission adopted revised European Sustainability Reporting Standards, amending
          the first set adopted in 2023, together with a voluntary standard for undertakings outside the scope of the CSRD. The revised
          standards are subject to a scrutiny period by the European Parliament and Council and, as reported by several advisers,
          apply to financial years beginning on or after 1 January 2027. The Commission describes a substantial reduction in
          mandatory datapoints. Treat the exact entry-into-force date as provisional until publication in the Official Journal.
        </p>
        <h2>Why effective dates belong in the data model</h2>
        <p>
          A gap analysis is only as current as its requirement list. Veridion stores requirement catalogues as versioned files with
          effective dates: its GRI 302 and 305 (2016) set is marked for reports published before 1 January 2027, and a GRI 102 and
          103 (2025) set is available as a draft for early adopters. Every assessment records which catalogue version it used, so a
          finding made today can still be explained after the standards change.
        </p>
      </>
    ),
    sources: [
      { label: "GRI — GRI 102: Climate Change 2025", url: "https://www.globalreporting.org/publications/documents/english/gri-102-climate-change-2025/" },
      { label: "GRI — GRI 103: Energy 2025, frequently asked questions (June 2025)", url: "https://www.globalreporting.org/media/mead5ytn/gri-103-energy-2025-frequently-asked-questions-faqs.pdf" },
      { label: "Jones Day — GRI releases new climate and energy standards", url: "https://trendingnowinesg.jonesday.com/post/102kqs7/gri-releases-new-climate-and-energy-standards-significant-reporting-changes-ahe" },
      { label: "Cooley — European Commission adopts revised EU CSRD reporting standards (July 2026)", url: "https://www.cooley.com/news/insight/2026/2026-07-21-european-commission-adopts-revised-eu-csrd-reporting-standards" },
      { label: "EY — European Commission adopts revised ESRS for sustainability reporting", url: "https://www.ey.com/en_gl/technical/csrd-technical-resources/eu-adopts-revised-esrs-for-sustainability-reporting" },
    ],
  },
];

export function articleBySlug(slug: string): Article | undefined {
  return articles.find((a) => a.slug === slug);
}
