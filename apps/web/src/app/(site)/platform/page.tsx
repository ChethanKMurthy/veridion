import type { Metadata } from "next";
import Link from "next/link";
import { Container, CtaBand, Masthead } from "@/components/site/chrome";
import { BenchmarkPreview, ConflictPreview, ExplorerPreview } from "@/components/site/previews";
import { ArrowRight } from "@/components/ui/icons";
import { StatusLabel } from "@/components/ui/status";
import { highlights } from "@/lib/highlights";

export const metadata: Metadata = {
  title: "Platform",
  description:
    "Document intelligence, versioned requirement mapping, the Evidence Explorer, peer intelligence, remediation and reproducible reports — one traceable workflow.",
};

const modules = [
  {
    id: "documents",
    title: "Document intelligence",
    body: "Upload annual reports, sustainability reports and policies as PDF. Veridion extracts passages, headings, tables and table rows, keeps the page and position of each, and reads scanned pages with OCR. Every value is stored with its unit and reporting period.",
    points: ["Page-level provenance for every passage", "Tables split into citeable rows", "OCR pages marked with their confidence", "Running headers and footers removed", "Document versions kept, never overwritten"],
  },
  {
    id: "requirements",
    title: "Versioned requirement catalogues",
    body: "Requirements are structured into weighted elements — a value, its period, the boundary, the methodology — each with a defined evidence check. Catalogues carry versions and effective dates, and a version never changes once it has been used.",
    points: ["GRI 302 and 305 (2016) climate and energy set", "GRI 102 and 103 (2025) draft for early adoption", "Applicability decisions recorded with a rationale", "Revisions published as new versions with a changelog"],
  },
  {
    id: "assessment",
    title: "Assessment",
    body: "Deterministic checks decide numbers, units and periods. An optional language model reviews whether the wording actually establishes each element. It can only cite passages Veridion found, citations are validated, and it can never override a detected conflict.",
    points: ["Five statuses, each with its own shape", "Cross-document conflict detection after unit conversion", "Rules-only mode for fully deterministic runs", "Model disagreements routed to human review"],
  },
  {
    id: "remediation",
    title: "Remediation",
    body: "Every gap becomes an action with a title, detail, effort and dependencies, ranked by importance × gap × urgency. Actions persist across runs; when a later run no longer shows the gap, the action is marked for a person to confirm and close.",
    points: ["Owners, due dates and status", "Dependencies between actions", "Visible priority components", "Closed only by a person"],
  },
  {
    id: "reports",
    title: "Reports and evidence packages",
    body: "Export a printable report, a CSV of findings, Markdown, or a JSON evidence package that records document hashes, catalogue and engine versions, every finding, its evidence and its review history.",
    points: ["Print-ready A4 report", "Machine-readable evidence package", "Assessment history and change attribution", "Append-only audit log"],
  },
];

export default function PlatformPage() {
  const h = highlights;
  return (
    <>
      <Masthead
        title="One workflow, from a folder of PDFs to findings you can defend."
        lead="Veridion connects documents, requirements, evidence, peers and actions in a single record, so every conclusion can be traced back to the page it came from."
      >
        <div className="flex flex-wrap gap-3">
          <Link href="/demo" className="inline-flex h-12 items-center gap-2 rounded-sm bg-on-dark px-5 text-[0.95rem] font-medium text-obsidian hover:bg-white">
            Explore the platform <ArrowRight size={16} />
          </Link>
          <Link href="/platform/evidence-explorer" className="inline-flex h-12 items-center rounded-sm border border-rule-dark-strong px-5 text-[0.95rem] text-on-dark hover:border-on-dark-muted">
            The Evidence Explorer
          </Link>
        </div>
      </Masthead>

      <section className="bg-canvas">
        <Container className="py-16 lg:py-24">
          <ol className="grid gap-px overflow-hidden rounded-sm border border-rule bg-rule sm:grid-cols-2 lg:grid-cols-5">
            {modules.map((m, i) => (
              <li key={m.id} className="bg-surface">
                <a href={`#${m.id}`} className="block h-full p-5 hover:bg-canvas">
                  <span className="tnum text-meta text-ink-muted">{String(i + 1).padStart(2, "0")}</span>
                  <span className="mt-2 block text-ui font-medium text-ink">{m.title}</span>
                </a>
              </li>
            ))}
          </ol>
          <p className="mt-4 text-ui-sm text-ink-muted">
            The five stages run in order for every assessment. Each one records what it did, so the result can be reproduced and
            explained.
          </p>
        </Container>
      </section>

      {modules.map((m, i) => (
        <section key={m.id} id={m.id} className={i % 2 === 0 ? "border-t border-rule bg-surface" : "border-t border-rule bg-canvas"}>
          <Container className="grid scroll-mt-20 gap-12 py-16 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)] lg:py-24">
            <div>
              <h2 className="font-display text-[clamp(1.9rem,3.2vw,2.7rem)] leading-[1.1] tracking-[-0.01em] text-ink">{m.title}</h2>
              <p className="mt-5 text-body text-ink-muted">{m.body}</p>
              <ul className="mt-7 space-y-2 border-t border-rule pt-5">
                {m.points.map((p) => (
                  <li key={p} className="flex gap-3 text-ui text-ink">
                    <span className="mt-2 size-1 shrink-0 rounded-full bg-ink" aria-hidden="true" />
                    {p}
                  </li>
                ))}
              </ul>
            </div>
            <div className="min-w-0 lg:pt-2">
              {m.id === "documents" ? <ConflictPreview /> : null}
              {m.id === "requirements" ? (
                <div className="rounded-sm border border-rule bg-surface">
                  <div className="border-b border-rule px-5 py-3">
                    <p className="text-ui font-medium text-ink">GRI 305-1 · Direct (Scope 1) GHG emissions</p>
                    <p className="font-mono text-[0.72rem] text-ink-muted">gri-302-305-2016@1.1.0 · effective to 31 Dec 2026</p>
                  </div>
                  <table className="w-full text-left text-ui-sm">
                    <tbody>
                      {[
                        ["Gross Scope 1 value (tCO₂e)", "3", "Typed value for the period"],
                        ["Reporting period stated with the figure", "2", "Period stated with the value"],
                        ["Consolidation approach", "2", "Disclosure wording"],
                        ["Standards or methodology used", "1", "Disclosure wording"],
                        ["Gases included", "1", "Disclosure wording"],
                        ["Emission factor and GWP sources", "1", "Disclosure wording"],
                        ["Base year, where applicable", "1", "Disclosure wording"],
                        ["Biogenic CO₂ reported separately", "1", "Added in v1.1.0"],
                      ].map(([label, weight, check]) => (
                        <tr key={label} className="border-b border-rule last:border-0">
                          <td className="px-5 py-2.5 text-ink">{label}</td>
                          <td className="tnum px-3 py-2.5 text-right text-ink-muted">×{weight}</td>
                          <td className="px-5 py-2.5 text-ink-muted">{check}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : null}
              {m.id === "assessment" ? (
                <div className="on-dark rounded-sm bg-obsidian p-4"><ExplorerPreview rows={6} /></div>
              ) : null}
              {m.id === "remediation" && h.conflict?.action ? (
                <div className="rounded-sm border border-rule bg-surface p-5">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="text-ui font-medium text-ink">{h.conflict.action.title}</p>
                      <p className="mt-1.5 text-ui-sm leading-relaxed text-ink-muted">{h.conflict.action.detail}</p>
                    </div>
                    <span className="tnum shrink-0 text-[1.4rem] font-semibold text-ink">{h.conflict.action.priority_score.toFixed(2)}</span>
                  </div>
                  <p className="mt-4 border-t border-rule pt-3 text-meta text-ink-muted">
                    {h.conflict.action.priority_components.explanation}
                  </p>
                  <p className="mt-2 flex items-center gap-2 text-meta text-ink-muted">
                    Linked to <StatusLabel status="conflicting" short /> {h.conflict.display_code} · {h.conflict.action.effort} effort
                  </p>
                </div>
              ) : null}
              {m.id === "reports" ? (
                <div className="overflow-hidden rounded-sm border border-rule bg-surface p-6 font-mono text-[0.72rem] leading-relaxed text-ink-muted">
                  <p className="text-ink">{"{"}</p>
                  <p className="pl-4">&quot;format&quot;: &quot;veridion.evidence-package/1&quot;,</p>
                  <p className="pl-4">&quot;run&quot;: {"{"} &quot;id&quot;: &quot;{h.run.id}&quot;, &quot;mode&quot;: &quot;{h.run.mode}&quot; {"}"},</p>
                  <p className="pl-4">&quot;requirement_set&quot;: &quot;{h.run.requirement_set_id}&quot;,</p>
                  <p className="pl-4">&quot;documents&quot;: [ {"{"} &quot;sha256&quot;: &quot;…&quot;, &quot;version&quot;: 1 {"}"} ],</p>
                  <p className="pl-4">&quot;findings&quot;: [ {"{"} &quot;status&quot;: &quot;conflicting&quot;, &quot;evidence&quot;: [ … ], &quot;reviews&quot;: [ … ] {"}"} ],</p>
                  <p className="pl-4">&quot;limitations&quot;: [ &quot;Absence of evidence is not evidence of non-compliance.&quot; ]</p>
                  <p className="text-ink">{"}"}</p>
                </div>
              ) : null}
            </div>
          </Container>
        </section>
      ))}

      <section className="border-t border-rule bg-surface">
        <Container className="grid gap-12 py-16 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)] lg:py-24">
          <BenchmarkPreview />
          <div>
            <h2 className="font-display text-[clamp(1.9rem,3.2vw,2.7rem)] leading-[1.1] tracking-[-0.01em] text-ink">Peer intelligence</h2>
            <p className="mt-5 text-body text-ink-muted">
              Compare two or three companies on the metrics they disclose, with units aligned and every limit on the comparison
              stated beside the number.
            </p>
            <Link href="/intelligence" className="mt-7 inline-flex items-center gap-2 text-[0.95rem] font-medium text-ink underline decoration-rule-strong underline-offset-4 hover:decoration-ink">
              How peer intelligence works <ArrowRight size={16} />
            </Link>
          </div>
        </Container>
      </section>

      <CtaBand title="See the workflow end to end." body="The demo workspace contains three fictional companies, two assessment runs and a catalogue revision you can compare." />
    </>
  );
}
