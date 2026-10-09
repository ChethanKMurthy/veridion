import type { Metadata } from "next";
import Link from "next/link";
import { Container, Masthead } from "@/components/site/chrome";

export const metadata: Metadata = {
  title: "Help centre",
  description: "Answers to common questions about accounts, documents, assessments, findings, exports and plans.",
};

const groups: { title: string; items: [string, React.ReactNode][] }[] = [
  {
    title: "Getting started",
    items: [
      ["Where do I begin?", <>Create a company, upload its PDFs on the Documents tab, then run an assessment from the Evidence tab. The <Link href="/documentation#getting-started">getting started guide</Link> walks through it.</>],
      ["Can I try it without uploading anything?", <>Yes. The <Link href="/demo">interactive demo</Link> is a recorded workspace with fictional companies. Changes you make there stay in your browser tab.</>],
    ],
  },
  {
    title: "Documents",
    items: [
      ["Which files can I upload?", "PDF files up to 50 MB. Scanned pages are read with OCR. Password-protected files are rejected."],
      ["My document is stuck on “processing”.", "Processing usually takes seconds to a few minutes depending on length and scanned pages. If it fails, the error is shown in the documents list with a Retry button."],
      ["How do I replace a document with a corrected version?", "Use “New version” on the documents list. Earlier assessments keep citing the version they used; findings that cite the old version are marked for reassessment."],
      ["Why can't I delete a document?", "Documents that findings cite cannot be deleted, so past assessments stay auditable. Upload a new version instead."],
    ],
  },
  {
    title: "Assessments and findings",
    items: [
      ["What do the statuses mean?", <>Supported, partially supported, evidence not found, conflicting evidence and human review required. Each is defined on the <Link href="/methodology#assessment">methodology</Link> page.</>],
      ["Why does a finding say “evidence not found” when the company does report this?", "The disclosure may be in a document that has not been uploaded, or worded differently from what the checks expect. Upload the document, or record an override with your reason."],
      ["What is the difference between rules only and rules + model?", "Rules-only runs are deterministic and send nothing externally. Rules + model adds a language model that reviews wording and drafts the rationale, under the constraints described on the AI governance page."],
      ["How do I correct a finding?", "Open the finding and use Review: accept it, override the status with a reason, or comment. The original assessment is kept beside your decision."],
      ["A requirement does not apply to this company.", "Record an applicability decision with a rationale. Later runs exclude the requirement and list it as not applicable."],
    ],
  },
  {
    title: "Exports and plans",
    items: [
      ["How do I share results?", "Open the report for a run to print or save it as PDF, or download CSV, Markdown or the JSON evidence package."],
      ["I hit a plan limit.", <>The message names the limit. <Link href="/pricing">Compare plans</Link> or <Link href="/contact?topic=sales">contact sales</Link>.</>],
    ],
  },
];

export default function HelpPage() {
  return (
    <>
      <Masthead title="Help centre" lead="Answers to common questions. If yours is not here, the support team will help." />
      <Container className="grid gap-12 py-16 lg:grid-cols-[minmax(0,1fr)_18rem] lg:py-24">
        <div className="space-y-12">
          {groups.map((g) => (
            <section key={g.title}>
              <h2 className="font-display text-[1.9rem] text-ink">{g.title}</h2>
              <div className="mt-4 divide-y divide-rule border-y border-rule">
                {g.items.map(([q, a]) => (
                  <details key={q} className="group py-4">
                    <summary className="flex cursor-pointer list-none items-start justify-between gap-6 text-ui font-medium text-ink [&::-webkit-details-marker]:hidden">
                      <span>{q}</span>
                      <span aria-hidden="true" className="text-ink-muted transition-transform group-open:rotate-45">+</span>
                    </summary>
                    <div className="mt-2 max-w-3xl text-ui leading-relaxed text-ink-muted [&_a]:text-ink [&_a]:underline [&_a]:underline-offset-2">{a}</div>
                  </details>
                ))}
              </div>
            </section>
          ))}
        </div>
        <aside className="space-y-4 lg:sticky lg:top-24 lg:self-start">
          <div className="rounded-sm border border-rule bg-surface p-5">
            <p className="text-ui font-medium text-ink">Still stuck?</p>
            <p className="mt-1.5 text-ui-sm text-ink-muted">Tell us what happened, and include the run or document ID if you have one.</p>
            <Link href="/contact?topic=support" className="mt-4 inline-flex h-9 items-center rounded-sm bg-obsidian px-3.5 text-ui font-medium text-on-dark hover:bg-graphite-2">
              Contact support
            </Link>
          </div>
          <Link href="/documentation" className="block text-ui-sm font-medium text-ink underline decoration-rule-strong underline-offset-2">
            Read the documentation
          </Link>
        </aside>
      </Container>
    </>
  );
}
