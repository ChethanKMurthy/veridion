import { Suspense } from "react";
import { CompanyFrame } from "@/components/app/company-frame";
import { ScreenSkeleton } from "@/components/ui/feedback";

export default function CompanyLayout({ children }: { children: React.ReactNode }) {
  return (
    <Suspense fallback={<ScreenSkeleton />}>
      <CompanyFrame>{children}</CompanyFrame>
    </Suspense>
  );
}
