/**
 * Plan presentation for the pricing page. Limits mirror the enforced values in
 * apps/api/src/veridion/services/entitlements.py — keep the two in sync.
 */

export type PlanCard = {
  key: "explorer" | "professional" | "enterprise";
  name: string;
  audience: string;
  price: string;
  priceNote: string;
  cta: { label: string; href: string };
  limits: [string, string][];
  includes: string[];
};

export const plans: PlanCard[] = [
  {
    key: "explorer",
    name: "Explorer",
    audience: "For individual analysts evaluating the platform.",
    price: "No charge",
    priceNote: "During the pilot",
    cta: { label: "Start exploring", href: "/sign-up" },
    limits: [
      ["Companies", "3"],
      ["Documents", "10"],
      ["Pages per document", "150"],
      ["Assessment runs per month", "15"],
      ["Model-assisted runs per month", "3"],
      ["Seats", "1"],
    ],
    includes: ["Evidence Explorer and evidence trails", "Peer comparisons", "Report, CSV, Markdown and JSON exports"],
  },
  {
    key: "professional",
    name: "Professional",
    audience: "For analysts and consultants running recurring assessments.",
    price: "Pilot pricing",
    priceNote: "On request",
    cta: { label: "Request access", href: "/request-access?plan=professional" },
    limits: [
      ["Companies", "50"],
      ["Documents", "500"],
      ["Pages per document", "600"],
      ["Assessment runs per month", "300"],
      ["Model-assisted runs per month", "150"],
      ["Seats", "5"],
    ],
    includes: ["Everything in Explorer", "Assessment history and run comparison", "Reviewer and viewer roles", "Standard support"],
  },
  {
    key: "enterprise",
    name: "Enterprise",
    audience: "For organizations with specific governance and operational needs.",
    price: "Custom agreement",
    priceNote: "Agreed usage limits",
    cta: { label: "Contact enterprise sales", href: "/contact?topic=enterprise" },
    limits: [
      ["Companies", "Agreed"],
      ["Documents", "Agreed"],
      ["Pages per document", "Agreed"],
      ["Assessment runs per month", "Agreed"],
      ["Model-assisted runs per month", "Agreed"],
      ["Seats", "Agreed"],
    ],
    includes: ["Everything in Professional", "Security and procurement review", "Choice of model provider, or rules-only", "Contracted support options"],
  },
];
