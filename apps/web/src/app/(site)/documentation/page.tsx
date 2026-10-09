import type { Metadata } from "next";
import Link from "next/link";
import { Container, Masthead } from "@/components/site/chrome";

export const metadata: Metadata = {
  title: "Documentation",
  description: "Getting started with Veridion, the concepts behind it, exports, the REST API and current limits.",
};

const toc = [
  ["getting-started", "Getting started"],
  ["concepts", "Concepts"],
  ["assessments", "Running assessments"],
  ["reviewing", "Reviewing findings"],
  ["peers", "Comparing peers"],
  ["exports", "Exports"],
  ["api", "API"],
  ["limits", "Limits"],
];

const endpoints: [string, string, string][] = [
  ["POST", "/api/v1/auth/login", "Sign in; returns your profile and sets the session"],
  ["GET", "/api/v1/companies", "List companies with document counts and the latest run"],
  ["POST", "/api/v1/companies/{id}/documents", "Upload a PDF (multipart); processing runs in the background"],
  ["GET", "/api/v1/documents/{id}/passages", "Extracted passages with page, position and values"],
  ["GET", "/api/v1/requirement-sets", "Available requirement catalogues and their status"],
  ["POST", "/api/v1/companies/{id}/runs", "Start an assessment run"],
  ["GET", "/api/v1/runs/{id}/findings", "Findings for a run, with review state"],
  ["GET", "/api/v1/findings/{id}", "The full evidence trail for one finding"],
  ["POST", "/api/v1/findings/{id}/reviews", "Accept, override or comment on a finding"],
  ["GET", "/api/v1/runs/{id}/diff", "What changed since another run, and why"],
  ["GET", "/api/v1/companies/{id}/benchmark", "Peer comparison with comparability notes"],
  ["GET", "/api/v1/runs/{id}/export?format=json", "Evidence package (also csv, md)"],
];

function H2({ id, children }: { id: string; children: React.ReactNode }) {
  return <h2 id={id} className="scroll-mt-24">{children}</h2>;
}

export default function DocumentationPage() {
  return (
    <>
      <Masthead title="Documentation" lead="How to use Veridion, the concepts behind it, and the API that powers it." />
      <Container className="py-16 lg:py-24">
        <div className="grid gap-12 lg:grid-cols-[14rem_minmax(0,1fr)]">
          <nav aria-label="On this page" className="lg:sticky lg:top-24 lg:self-start">
            <ol className="space-y-1.5 border-l border-rule pl-4 text-ui-sm">
              {toc.map(([id, l]) => (
                <li key={id}>
                  <a href={`#${id}`} className="text-ink-muted hover:text-ink">{l}</a>
                </li>
              ))}
            </ol>
          </nav>
          <div className="prose-veridion max-w-[72ch]">
            <H2 id="getting-started">Getting started</H2>
            <ol>
              <li><strong>Create a workspace.</strong> <Link href="/sign-up">Sign up</Link> with your work email. You become the owner of a new organization.</li>
              <li><strong>Add a company.</strong> Give its name and financial year end — the year end decides how periods such as FY2025 are dated.</li>
              <li><strong>Upload documents.</strong> Start with the latest annual report and sustainability report. Set each document&apos;s type and reporting period.</li>
              <li><strong>Run an assessment.</strong> On the Evidence tab, choose a requirement catalogue, the period, and rules-only or rules + model.</li>
              <li><strong>Review the findings.</strong> Open each finding to follow its trail, open the source passage, and accept, override or comment.</li>
              <li><strong>Act on the gaps.</strong> Assign owners and dates on the Actions tab, then export a report.</li>
            </ol>

            <H2 id="concepts">Concepts</H2>
            <h3>Companies and peers</h3>
            <p>A company has documents, assessment runs and actions. Mark up to ten other companies as its peers to compare them.</p>
            <h3>Documents and versions</h3>
            <p>
              Each upload is an immutable version identified by its SHA-256 hash. Uploading a corrected file as a new version keeps the old
              one, so earlier findings still point to what they cited.
            </p>
            <h3>Passages and evidence identifiers</h3>
            <p>
              Documents are split into passages — paragraphs, headings, list items, tables and table rows — each with a page, a bounding
              box and a stable identifier such as <code>ev_93a18ca53e4aace0f313</code>. Values found in passages are stored with their unit,
              normalised unit and period.
            </p>
            <h3>Requirement catalogues</h3>
            <p>
              A catalogue is a versioned set of requirements, each made of weighted elements with defined evidence checks. Catalogues have
              effective dates and a review status; draft catalogues are labelled.
            </p>
            <h3>Runs, findings and statuses</h3>
            <p>
              An assessment run evaluates every applicable requirement in one catalogue against a company&apos;s current documents for one
              period, producing one finding per requirement with a status, a completeness score, a rationale, element results and linked
              evidence. See the <Link href="/methodology">methodology</Link> for the rules.
            </p>
            <h3>Actions</h3>
            <p>Gaps become actions ranked by importance × gap × urgency. Actions persist across runs and are closed by a person.</p>

            <H2 id="assessments">Running assessments</H2>
            <p>
              All documents must have finished processing before a run starts. Runs execute in the background; progress is shown on the
              Evidence tab. Set a reporting deadline to rank actions by urgency. To exclude a requirement that does not apply, record an
              applicability decision with a rationale before running.
            </p>

            <H2 id="reviewing">Reviewing findings</H2>
            <p>
              Select a row in the Evidence Explorer, or use the arrow keys and Enter. The trail shows the requirement and its elements, the
              evidence on the page, the rationale with clickable citations, the gap and the linked action. An override needs a reason;
              comments never change the status.
            </p>

            <H2 id="peers">Comparing peers</H2>
            <p>
              The Peers tab aligns units, shows each company&apos;s reporting period and consolidation approach, and lists comparability
              notes beside each value. Values not disclosed are shown as such.
            </p>

            <H2 id="exports">Exports</H2>
            <ul>
              <li><strong>Report</strong> — a printable page; use your browser&apos;s print dialog to save it as PDF.</li>
              <li><strong>CSV</strong> — one row per finding with status, review state, completeness, priority and primary source.</li>
              <li><strong>Markdown</strong> — the report as text.</li>
              <li>
                <strong>Evidence package (JSON)</strong> — format <code>veridion.evidence-package/1</code>: the run manifest with document
                hashes and versions, every finding with its elements, evidence passages and reviews, the actions, and the limitations.
              </li>
            </ul>

            <H2 id="api">API</H2>
            <p>
              The REST API lives under <code>/api/v1</code>, and an interactive reference is served at <code>/api/docs</code> on every
              deployment. Browser sessions use an HttpOnly cookie; other clients send the session token as{" "}
              <code>Authorization: Bearer …</code>. Requests that change data from a browser must include the header{" "}
              <code>X-Veridion-Client: web</code>.
            </p>
            <table>
              <thead>
                <tr>
                  <th>Method</th>
                  <th>Path</th>
                  <th>Purpose</th>
                </tr>
              </thead>
              <tbody>
                {endpoints.map(([m, p, d]) => (
                  <tr key={p}>
                    <td><code>{m}</code></td>
                    <td><code>{p}</code></td>
                    <td>{d}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            <H2 id="limits">Limits</H2>
            <p>
              Uploads are limited to PDF files of up to 50 MB. Plan limits on companies, documents, pages per document, runs and seats are
              listed on the <Link href="/pricing">pricing</Link> page and in your workspace settings. Exceeding a limit returns HTTP 402 with
              a message naming the limit.
            </p>
          </div>
        </div>
      </Container>
    </>
  );
}
