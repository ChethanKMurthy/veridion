import type { Metadata } from "next";
import { Suspense } from "react";
import { CompanyOverviewScreen } from "@/components/app/screens/company-overview";
import { ScreenSkeleton } from "@/components/ui/feedback";

export const metadata: Metadata = { title: "Company intelligence" };

export default function Page() {
  return (
    <Suspense fallback={<ScreenSkeleton />}>
      <CompanyOverviewScreen />
    </Suspense>
  );
}
