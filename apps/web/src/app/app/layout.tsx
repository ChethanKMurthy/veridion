import type { Metadata } from "next";
import { LiveWorkspace } from "@/components/app/workspace";

export const metadata: Metadata = {
  title: { default: "Workspace", template: "%s · Veridion" },
  robots: { index: false, follow: false },
};

export default function WorkspaceLayout({ children }: { children: React.ReactNode }) {
  return <LiveWorkspace>{children}</LiveWorkspace>;
}
