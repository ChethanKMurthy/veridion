import type { Metadata } from "next";
import { Suspense } from "react";
import { DocumentsScreen } from "@/components/app/screens/documents";
import { ScreenSkeleton } from "@/components/ui/feedback";

export const metadata: Metadata = { title: "Documents" };

export default function Page() {
  return (
    <Suspense fallback={<ScreenSkeleton />}>
      <DocumentsScreen />
    </Suspense>
  );
}
