import type { Metadata } from "next";
import { Masthead, PolicyBody } from "@/components/site/chrome";
import { site } from "@/lib/site";

export const metadata: Metadata = {
  title: "Subprocessors",
  description: "External services that may process customer data in Veridion, and the conditions under which they do.",
};

export default function SubprocessorsPage() {
  return (
    <>
      <Masthead title="Subprocessors" lead="Third parties that may process customer data on Veridion's behalf." />
      <PolicyBody>
        <table>
          <thead>
            <tr>
              <th>Provider</th>
              <th>Purpose</th>
              <th>Data</th>
              <th>Location</th>
            </tr>
          </thead>
          <tbody>
            {site.subprocessors.map((s) => (
              <tr key={s.name}>
                <td>{s.name}</td>
                <td>{s.purpose}</td>
                <td>
                  {s.data}
                  <br />
                  <em>{s.condition}</em>
                </td>
                <td>{s.location}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <h2>Hosting</h2>
        <p>
          Hosting, database and file-storage providers depend on the deployment and will be listed here when Veridion operates a
          production service. Self-hosted deployments use the infrastructure of the organization running them.
        </p>
        <h2>Changes</h2>
        <p>We will update this page before adding a subprocessor that processes customer documents.</p>
      </PolicyBody>
    </>
  );
}
