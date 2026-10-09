import type { Metadata } from "next";
import Link from "next/link";
import { Masthead, PolicyBody } from "@/components/site/chrome";

export const metadata: Metadata = {
  title: "AI governance",
  description: "What the language model in Veridion may and may not do, how its output is checked, its known failure modes, and the human oversight around it.",
};

export default function AiGovernancePage() {
  return (
    <>
      <Masthead
        title="AI governance"
        lead="Veridion uses a language model as a reviewer, not an authority. These are the rules it operates under and the ways it can still go wrong."
      />
      <PolicyBody>
        <h2>The model&apos;s job</h2>
        <p>
          In AI-assisted runs, the model reads a requirement, the result of each deterministic check, and a short list of candidate
          passages, then judges whether the wording actually establishes each element. It drafts the rationale shown on the finding.
        </p>

        <h2>What it cannot do</h2>
        <ul>
          <li>It cannot change data, take actions or call tools. Its only output is a structured JSON answer.</li>
          <li>It cannot cite a passage it was not shown. Every citation is checked; unknown identifiers are discarded and recorded.</li>
          <li>It cannot decide numbers, units or periods. If it disagrees with an extracted value, the finding goes to human review instead.</li>
          <li>It cannot override a detected conflict between documents.</li>
        </ul>

        <h2>Which model, and when</h2>
        <p>
          The model is configurable per deployment. The default is <code>openai/gpt-oss-120b</code> served by Groq, called with
          temperature zero. A deployment can use another compatible provider, a model running on its own infrastructure, or no model
          at all — rules-only assessments are fully deterministic. Every run records the provider, model and prompt version used.
        </p>

        <h2>Known failure modes</h2>
        <table>
          <thead>
            <tr>
              <th>Risk</th>
              <th>Safeguard</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Invented citations</td>
              <td>Citations are validated against the passages shown; invalid ones are discarded and counted.</td>
            </tr>
            <tr>
              <td>Overconfident or wrong judgements</td>
              <td>Deterministic checks decide figures; sharp disagreements and low-confidence answers are routed to human review.</td>
            </tr>
            <tr>
              <td>Instructions hidden in documents</td>
              <td>Passage text is presented as data, the prompt says so explicitly, and the model has no tools to act on such instructions.</td>
            </tr>
            <tr>
              <td>Provider outage or error</td>
              <td>The requirement falls back to the rules-only result and is flagged for review.</td>
            </tr>
            <tr>
              <td>Behaviour changing between model versions</td>
              <td>Runs record the model and prompt version; responses are cached per version; the evaluation suite can be re-run.</td>
            </tr>
          </tbody>
        </table>

        <h2>Human oversight</h2>
        <p>
          Reviewers can accept a finding, override its status with a recorded reason, or comment. The original assessment is never
          overwritten. Model adjustments to rule checks are listed on each finding, so a reviewer can see exactly where the model
          changed the outcome.
        </p>

        <h2>Measurement</h2>
        <p>
          Rules-only and AI-assisted modes are measured against the same labelled dataset, and the results — including failure
          cases — are published on the <Link href="/methodology#evaluation">methodology</Link> page.
        </p>

        <h2>Appropriate use</h2>
        <ul>
          <li>Veridion supports evidence review. It does not provide legal advice or make compliance determinations.</li>
          <li>Findings describe the documents provided; conclusions about a company should be reached by a qualified person.</li>
          <li>It should not be used to make decisions about individuals.</li>
        </ul>
      </PolicyBody>
    </>
  );
}
