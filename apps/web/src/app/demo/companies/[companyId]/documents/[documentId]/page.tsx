import type { Metadata } from "next";
import { Suspense } from "react";
import { DocumentViewerScreen } from "@/components/app/screens/document-viewer";
import { ScreenSkeleton } from "@/components/ui/feedback";

export const metadata: Metadata = { title: "Document" };

export default function Page() {
  return (
    <Suspense fallback={<ScreenSkeleton />}>
      <DocumentViewerScreen />
    </Suspense>
  );
}
