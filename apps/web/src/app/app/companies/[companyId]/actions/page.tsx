import type { Metadata } from "next";
import { Suspense } from "react";
import { ActionsScreen } from "@/components/app/screens/actions";
import { ScreenSkeleton } from "@/components/ui/feedback";

export const metadata: Metadata = { title: "Remediation" };

export default function Page() {
  return (
    <Suspense fallback={<ScreenSkeleton />}>
      <ActionsScreen />
    </Suspense>
  );
}
