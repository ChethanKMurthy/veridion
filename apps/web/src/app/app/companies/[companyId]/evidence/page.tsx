import type { Metadata } from "next";
import { Suspense } from "react";
import { EvidenceExplorer } from "@/components/app/evidence-explorer";
import { ScreenSkeleton } from "@/components/ui/feedback";

export const metadata: Metadata = { title: "Evidence Explorer" };

export default function Page() {
  return (
    <Suspense fallback={<ScreenSkeleton />}>
      <EvidenceExplorer />
    </Suspense>
  );
}
