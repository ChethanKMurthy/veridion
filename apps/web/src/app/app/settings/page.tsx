import type { Metadata } from "next";
import { Suspense } from "react";
import { SettingsScreen } from "@/components/app/screens/settings";
import { ScreenSkeleton } from "@/components/ui/feedback";

export const metadata: Metadata = { title: "Settings" };

export default function Page() {
  return (
    <Suspense fallback={<ScreenSkeleton />}>
      <SettingsScreen />
    </Suspense>
  );
}
