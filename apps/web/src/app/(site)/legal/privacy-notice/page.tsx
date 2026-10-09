import type { Metadata } from "next";
import Link from "next/link";
import { Masthead, PolicyBody } from "@/components/site/chrome";

export const metadata: Metadata = {
  title: "Privacy notice",
  description: "How Veridion collects, uses and protects personal data.",
};

export default function PrivacyNoticePage() {
  return (
    <>
      <Masthead title="Privacy notice" lead="What personal data Veridion collects, why, and the choices you have." />
      <PolicyBody>
        <h2>Who we are</h2>
        <p>
          Veridion is a product in development. Until the operating company is established, questions about this notice and requests
          about your data are handled through the <Link href="/contact?topic=privacy">contact form</Link>. The responsible entity will
          be named on this page and on the <Link href="/company/corporate-information">corporate information</Link> page.
        </p>

        <h2>What we collect</h2>
        <ul>
          <li><strong>Account data</strong> — your name, work email, organization and a hash of your password.</li>
          <li><strong>Content</strong> — documents you upload and information derived from them. These may contain personal data, for example names of company officers in an annual report.</li>
          <li><strong>Activity data</strong> — actions you take in a workspace, with timestamps; for sign-ins, the network address.</li>
          <li><strong>Enquiries</strong> — the details you send through our forms, and a one-way hash of your network address.</li>
          <li><strong>Cookies</strong> — one essential session cookie after you sign in. See the <Link href="/legal/cookies">cookie policy</Link>.</li>
        </ul>

        <h2>Why we use it</h2>
        <ul>
          <li>To provide your account and the service you request.</li>
          <li>To keep the service secure, including audit logs and abuse prevention.</li>
          <li>To reply to enquiries and, where you ask us to, to arrange demonstrations or pilots.</li>
          <li>To meet legal obligations that apply to us.</li>
        </ul>
        <p>We do not sell personal data, use it for advertising, or use customer documents to train models.</p>

        <h2>Who we share it with</h2>
        <p>
          Personal data is shared only with service providers that help run Veridion, listed on the{" "}
          <Link href="/trust/subprocessors">subprocessors</Link> page. In AI-assisted assessments, short passages from your documents —
          which may contain personal data — are sent to the model provider listed there, which may process them outside your country.
        </p>

        <h2>How long we keep it</h2>
        <p>
          Account and workspace data are kept while your account or workspace exists, and deleted when you ask us to delete them,
          subject to any legal obligation to retain records. Enquiries are kept as long as needed to handle them.
        </p>

        <h2>Your rights</h2>
        <p>
          Depending on where you live, you may have rights to access, correct, delete or export your personal data, to object to or
          restrict certain processing, and to complain to a data protection authority. To exercise them,{" "}
          <Link href="/contact?topic=privacy">contact us</Link>; we will respond within the time the applicable law requires.
        </p>

        <h2>Children</h2>
        <p>Veridion is a professional tool and is not intended for children.</p>

        <h2>Changes</h2>
        <p>We will update this notice when our practices change and show the date of the latest version.</p>
      </PolicyBody>
    </>
  );
}
