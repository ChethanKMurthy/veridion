import type { Metadata } from "next";
import Link from "next/link";
import { Masthead, PolicyBody } from "@/components/site/chrome";

export const metadata: Metadata = {
  title: "Terms of service",
  description: "The terms that apply to the Veridion website, demo and platform.",
};

export default function TermsPage() {
  return (
    <>
      <Masthead title="Terms of service" lead="The terms for using the Veridion website, the interactive demo and the platform, in plain language." />
      <PolicyBody>
        <h2>The service</h2>
        <p>
          Veridion is software for reviewing company disclosures: it extracts evidence from documents you provide, assesses it against
          requirement catalogues, compares companies and records the results. It is an early-stage product offered as a pilot. Features
          may change, and some may be withdrawn.
        </p>

        <h2>Accounts</h2>
        <p>
          You must give accurate account details and keep your password confidential. You are responsible for activity in your
          workspace, including by members you invite, and for choosing their roles.
        </p>

        <h2>Your content</h2>
        <p>
          You keep all rights in the documents and information you upload. You allow Veridion to store and process them only to
          provide the service to you — including, if you choose AI-assisted assessments, sending short passages to the model provider
          described on the <Link href="/trust/subprocessors">subprocessors</Link> page. You confirm that you have the right to upload
          what you upload.
        </p>

        <h2>Results are not advice</h2>
        <p>
          Findings describe the evidence in the documents provided. They are not legal, audit or investment advice and not a
          determination that any organization complies or fails to comply with any law or standard. Automated extraction and
          assessment can be wrong: verify material results against the source before relying on them. Requirement summaries are
          paraphrases; the official standards prevail.
        </p>

        <h2>Acceptable use</h2>
        <ul>
          <li>Do not attempt to access other organizations&apos; data or to bypass limits or security controls.</li>
          <li>Do not upload unlawful material, malware, or documents you are not entitled to share.</li>
          <li>Do not use the service to make decisions about individuals or to harass anyone.</li>
          <li>Do not overload the service or scrape it.</li>
        </ul>

        <h2>Demo content</h2>
        <p>
          The companies, documents and figures in the public demo are fictional and were created for demonstration. They do not
          describe any real organization.
        </p>

        <h2>Plans and fees</h2>
        <p>
          Explorer workspaces have no charge during the pilot, within published limits. Paid plans, when offered, will be governed by
          an order form or published price list stating fees, billing period, taxes and cancellation terms.
        </p>

        <h2>Availability and support</h2>
        <p>
          During the pilot the service is provided as is, without a service-level agreement. We aim to fix problems promptly and to
          give notice of planned changes that affect your data.
        </p>

        <h2>Ending use</h2>
        <p>
          You may stop using the service at any time and ask us to delete your workspace. We may suspend accounts that breach these
          terms. Before any deletion we initiate, we will give you a reasonable opportunity to export your data, unless the law or a
          security risk prevents it.
        </p>

        <h2>Liability</h2>
        <p>
          To the extent the law allows, Veridion is not liable for indirect or consequential losses, or for decisions made on the basis
          of results you did not verify. Nothing in these terms limits liability that cannot be limited by law.
        </p>

        <h2>Changes and governing law</h2>
        <p>
          We may update these terms and will note the date of each change on this page. The governing law, jurisdiction and contracting
          entity will be stated here when the operating company is established.
        </p>

        <h2>Contact</h2>
        <p>
          Questions about these terms: <Link href="/contact">contact us</Link>.
        </p>
      </PolicyBody>
    </>
  );
}
