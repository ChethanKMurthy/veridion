import type { Metadata } from "next";
import Link from "next/link";
import { Masthead, PolicyBody } from "@/components/site/chrome";

export const metadata: Metadata = {
  title: "Accessibility statement",
  description: "Veridion's accessibility target, the measures in place, known limitations and how to report a problem.",
};

export default function AccessibilityPage() {
  return (
    <>
      <Masthead title="Accessibility statement" lead="Veridion aims to meet WCAG 2.2 at level AA across the website, the demo and the platform." />
      <PolicyBody>
        <h2>What we do</h2>
        <ul>
          <li>Semantic HTML with labelled controls, a skip link and headings in order.</li>
          <li>Full keyboard operation: tables move with the arrow keys, panels and dialogs close with Escape, focus is always visible.</li>
          <li>Text colours chosen to meet at least 4.5:1 contrast against their backgrounds.</li>
          <li>Status is never shown by colour alone — every status has its own shape and a text label.</li>
          <li>Motion respects the reduced-motion setting, and no animation delays access to information.</li>
          <li>Evidence panels become full-height drawers on small screens.</li>
        </ul>

        <h2>Known limitations</h2>
        <ul>
          <li>Rendered PDF pages are images. The text Veridion extracted from each page is listed beside it and can be read by assistive technology, but the page image itself cannot.</li>
          <li>Wide data tables scroll horizontally on small screens.</li>
          <li>The accessibility of documents you upload depends on those documents.</li>
          <li>We have not yet commissioned an independent accessibility audit.</li>
        </ul>

        <h2>Report a problem</h2>
        <p>
          If something is difficult to use, please tell us through the{" "}
          <Link href="/contact?topic=accessibility">contact form</Link>, choosing “Accessibility”, and include the page and the
          assistive technology you use. We treat accessibility problems as defects.
        </p>
      </PolicyBody>
    </>
  );
}
