import type { Metadata } from "next";
import { Suspense } from "react";
import { DashboardScreen } from "@/components/app/screens/dashboard";
import { ScreenSkeleton } from "@/components/ui/feedback";

export const metadata: Metadata = { title: "Overview" };

export default function Page() {
  return (
    <Suspense fallback={<ScreenSkeleton />}>
      <DashboardScreen />
    </Suspense>
  );
}
