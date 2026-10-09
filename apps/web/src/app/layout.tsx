import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono, Libre_Caslon_Display, Libre_Caslon_Text } from "next/font/google";
import { site } from "@/lib/site";
import "./globals.css";

const geist = Geist({ variable: "--font-geist", subsets: ["latin"], display: "swap" });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"], display: "swap" });
const caslonDisplay = Libre_Caslon_Display({
  variable: "--font-caslon-display",
  weight: "400",
  subsets: ["latin"],
  display: "swap",
});
const caslonText = Libre_Caslon_Text({
  variable: "--font-caslon-text",
  weight: ["400", "700"],
  style: ["normal", "italic"],
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL(site.url),
  title: {
    default: "Veridion — Company intelligence, grounded in evidence",
    template: "%s · Veridion",
  },
  description:
    "Veridion turns company disclosures into traceable intelligence: every finding linked to its evidence, every gap explained, every recommendation justified.",
  applicationName: "Veridion",
  openGraph: {
    type: "website",
    siteName: "Veridion",
    title: "Veridion — Company intelligence, grounded in evidence",
    description:
      "Investigate claims, evaluate evidence, identify gaps and understand how organizations compare — with every conclusion traceable to its source page.",
  },
};

export const viewport: Viewport = {
  themeColor: "#101112",
  colorScheme: "light",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en-GB"
      className={`${geist.variable} ${geistMono.variable} ${caslonDisplay.variable} ${caslonText.variable}`}
    >
      <body className="min-h-dvh">
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[60] focus:bg-surface focus:px-4 focus:py-2 focus:text-ui focus:shadow-[var(--shadow-overlay)]"
        >
          Skip to content
        </a>
        {children}
      </body>
    </html>
  );
}
