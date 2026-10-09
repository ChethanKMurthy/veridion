import type { Metadata } from "next";
import { Suspense } from "react";
import { HistoryScreen } from "@/components/app/screens/history";
import { ScreenSkeleton } from "@/components/ui/feedback";

export const metadata: Metadata = { title: "Assessment history" };

export default function Page() {
  return (
    <Suspense fallback={<ScreenSkeleton />}>
      <HistoryScreen />
    </Suspense>
  );
}
