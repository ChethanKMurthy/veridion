import type { Metadata } from "next";
import { DemoWorkspace } from "@/components/app/workspace";

export const metadata: Metadata = {
  title: { default: "Interactive demo", template: "%s · Veridion demo" },
  description:
    "Explore a Veridion workspace with fictional companies: follow findings to their source pages, compare peers and act on gaps.",
};

export default function DemoLayout({ children }: { children: React.ReactNode }) {
  return <DemoWorkspace>{children}</DemoWorkspace>;
}
