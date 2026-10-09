import type { Metadata } from "next";
import { Suspense } from "react";
import { PeersScreen } from "@/components/app/screens/peers";
import { ScreenSkeleton } from "@/components/ui/feedback";

export const metadata: Metadata = { title: "Peer intelligence" };

export default function Page() {
  return (
    <Suspense fallback={<ScreenSkeleton />}>
      <PeersScreen />
    </Suspense>
  );
}
