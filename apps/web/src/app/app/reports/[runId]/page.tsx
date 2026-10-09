import type { Metadata } from "next";
import { Suspense } from "react";
import { ReportScreen } from "@/components/app/screens/report";
import { ScreenSkeleton } from "@/components/ui/feedback";

export const metadata: Metadata = { title: "Assessment report" };

export default function Page() {
  return (
    <Suspense fallback={<ScreenSkeleton />}>
      <ReportScreen />
    </Suspense>
  );
}
