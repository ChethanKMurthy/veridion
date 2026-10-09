import type { Metadata } from "next";
import { Suspense } from "react";
import { CompaniesScreen } from "@/components/app/screens/companies";
import { ScreenSkeleton } from "@/components/ui/feedback";

export const metadata: Metadata = { title: "Companies" };

export default function Page() {
  return (
    <Suspense fallback={<ScreenSkeleton />}>
      <CompaniesScreen />
    </Suspense>
  );
}
