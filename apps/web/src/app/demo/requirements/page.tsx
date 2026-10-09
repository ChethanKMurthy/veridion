import type { Metadata } from "next";
import { Suspense } from "react";
import { RequirementsScreen } from "@/components/app/screens/requirements";
import { ScreenSkeleton } from "@/components/ui/feedback";

export const metadata: Metadata = { title: "Requirement catalogues" };

export default function Page() {
  return (
    <Suspense fallback={<ScreenSkeleton />}>
      <RequirementsScreen />
    </Suspense>
  );
}
