import type { Metadata } from "next";
import { Masthead, PolicyBody } from "@/components/site/chrome";

export const metadata: Metadata = {
  title: "Cookie policy",
  description: "The cookies and browser storage Veridion uses.",
};

export default function CookiesPage() {
  return (
    <>
      <Masthead title="Cookie policy" lead="Veridion uses one essential cookie and no tracking." />
      <PolicyBody>
        <h2>Cookies</h2>
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Purpose</th>
              <th>Duration</th>
              <th>Type</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>
                <code>veridion_session</code>
              </td>
              <td>Keeps you signed in to the platform. Set only after you sign in.</td>
              <td>7 days</td>
              <td>Strictly necessary</td>
            </tr>
          </tbody>
        </table>
        <p>
          Because this cookie is strictly necessary for a service you request, it does not need consent. Veridion sets no analytics,
          advertising or social media cookies, so there is nothing to opt out of.
        </p>
        <h2>Browser storage</h2>
        <p>
          The public demo remembers which steps of the guided scenario you have completed using your browser&apos;s session storage. It
          never leaves your browser and is cleared when you close the tab.
        </p>
        <h2>Changes</h2>
        <p>If we ever add a non-essential cookie, we will update this page and ask for your consent first.</p>
      </PolicyBody>
    </>
  );
}
