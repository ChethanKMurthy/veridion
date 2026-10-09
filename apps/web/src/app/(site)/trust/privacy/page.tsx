import type { Metadata } from "next";
import Link from "next/link";
import { Masthead, PolicyBody } from "@/components/site/chrome";

export const metadata: Metadata = {
  title: "Data handling",
  description: "What data Veridion processes, where it goes, how long it is kept, and what is never done with it.",
};

export default function DataHandlingPage() {
  return (
    <>
      <Masthead title="Data handling" lead="A plain description of the data Veridion processes when you use the website and the platform." />
      <PolicyBody>
        <h2>What Veridion processes</h2>
        <table>
          <thead>
            <tr>
              <th>Data</th>
              <th>Why</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Account details: name, work email, organization, password hash</td>
              <td>To provide your account and workspace</td>
            </tr>
            <tr>
              <td>Documents you upload, and the passages, tables and values extracted from them</td>
              <td>To assess them and show the evidence behind each finding</td>
            </tr>
            <tr>
              <td>Assessments, findings, reviews and actions</td>
              <td>To provide the product and its history</td>
            </tr>
            <tr>
              <td>Activity records: actions taken, timestamps and, for sign-ins, the network address</td>
              <td>Security and the workspace audit log</td>
            </tr>
            <tr>
              <td>Usage counts: runs, pages processed, model tokens</td>
              <td>Plan limits and, in future, billing</td>
            </tr>
            <tr>
              <td>Website enquiries: name, email, organization and your message; a one-way hash of the network address</td>
              <td>To reply to you and to limit abuse of the form</td>
            </tr>
          </tbody>
        </table>

        <h2>Where it goes</h2>
        <p>
          Documents and data are stored in the database and file storage of the deployment you use. When an organization runs an
          AI-assisted assessment, the requirement text and up to twelve short passages per requirement are sent to the configured
          model provider for processing; see <Link href="/trust/subprocessors">subprocessors</Link>. Rules-only assessments send
          nothing to any external service.
        </p>

        <h2>What is never done with it</h2>
        <ul>
          <li>Veridion does not use customer documents to train models. Passages sent to a model provider in AI-assisted runs are processed under that provider&apos;s terms, listed on the <Link href="/trust/subprocessors">subprocessors</Link> page.</li>
          <li>Customer data is not sold, shared with advertisers, or used to profile individuals.</li>
          <li>Documents from one organization are never visible to another.</li>
        </ul>

        <h2>How long it is kept</h2>
        <p>
          Workspace data is kept while the workspace exists. To keep assessments auditable, a document that findings cite can be
          replaced but not deleted, and a company with assessment history cannot be deleted from the interface; to remove a whole
          workspace and its data, <Link href="/contact?topic=privacy">contact us</Link>. Model responses are cached so that a re-run
          on unchanged inputs gives the same result. Website enquiries are kept for as long as needed to handle them.
        </p>

        <h2>Cookies and browser storage</h2>
        <p>
          The platform sets one essential cookie, <code>veridion_session</code>, after you sign in. The public demo stores your
          progress through the guided scenario in your browser&apos;s session storage, which is cleared when you close the tab.
          Veridion uses no analytics, advertising or tracking cookies. See the <Link href="/legal/cookies">cookie policy</Link>.
        </p>

        <h2>Your choices</h2>
        <p>
          You can export your assessments at any time as reports, CSV, Markdown or a JSON evidence package. For access, correction or
          deletion of personal data, see the <Link href="/legal/privacy-notice">privacy notice</Link>.
        </p>
      </PolicyBody>
    </>
  );
}
