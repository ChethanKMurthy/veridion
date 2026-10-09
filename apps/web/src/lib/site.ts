/**
 * Public-facing company facts. Edit this file — not individual pages — when details change.
 *
 * Everything here is published on the website. Only add a value once it is true:
 * do not list a registered office, registration number, mailbox or certification
 * that does not exist yet. Pages render honest "not yet established" states for nulls.
 */

export type CorporateStatus = "in_development" | "incorporated";

export const site = {
  name: "Veridion",
  tagline: "Company intelligence, grounded in evidence.",
  url: process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000",
  year: 2026,

  corporate: {
    status: "in_development" as CorporateStatus,
    legalName: null as string | null,
    entityType: null as string | null,
    countryOfIncorporation: null as string | null,
    registrationNumber: null as string | null,
    registeredOffice: null as string | null,
    principalBusinessAddress: null as string | null,
    taxRegistrations: [] as string[],
    officers: [] as { name: string; role: string }[],
  },

  /** Mailboxes are listed only after they exist. Until then the contact form routes every enquiry. */
  mailboxes: {
    general: null as string | null,
    sales: null as string | null,
    support: null as string | null,
    privacy: null as string | null,
    security: null as string | null,
  },

  legal: {
    /** Set to true once a lawyer has reviewed the terms, privacy notice and cookie policy. */
    reviewed: false,
    lastUpdated: "9 October 2026",
  },

  support: {
    commitment:
      "A small team reads every enquiry. We reply as soon as we can, usually within a few business days. " +
      "We do not offer guaranteed response times yet.",
  },

  /** External services that may process customer data, shown on /trust/subprocessors. */
  subprocessors: [
    {
      name: "Groq, Inc.",
      purpose: "Model inference for AI-assisted assessments",
      data: "Requirement text and up to twelve short evidence passages per requirement, when AI-assisted mode is used",
      location: "United States",
      condition: "Only when an organization runs an AI-assisted assessment. Rules-only assessments send no data.",
    },
  ],
} as const;

export const nav = {
  primary: [
    { href: "/platform", label: "Platform" },
    { href: "/intelligence", label: "Intelligence" },
    { href: "/methodology", label: "Methodology" },
    { href: "/research", label: "Research" },
    { href: "/pricing", label: "Pricing" },
    { href: "/about", label: "About" },
  ],
  footer: [
    {
      title: "Platform",
      links: [
        { href: "/platform", label: "Overview" },
        { href: "/platform/evidence-explorer", label: "Evidence Explorer" },
        { href: "/intelligence", label: "Peer intelligence" },
        { href: "/methodology", label: "Methodology" },
        { href: "/pricing", label: "Pricing" },
      ],
    },
    {
      title: "Company",
      links: [
        { href: "/about", label: "About" },
        { href: "/company/corporate-information", label: "Corporate information" },
        { href: "/contact", label: "Contact" },
        { href: "/request-access", label: "Request access" },
      ],
    },
    {
      title: "Resources",
      links: [
        { href: "/demo", label: "Interactive demo" },
        { href: "/research", label: "Research" },
        { href: "/documentation", label: "Documentation" },
        { href: "/help", label: "Help centre" },
      ],
    },
    {
      title: "Trust & legal",
      links: [
        { href: "/trust/security", label: "Security" },
        { href: "/trust/ai-governance", label: "AI governance" },
        { href: "/legal/privacy-notice", label: "Privacy" },
        { href: "/legal/terms", label: "Terms" },
        { href: "/legal/accessibility", label: "Accessibility" },
      ],
    },
  ],
};
