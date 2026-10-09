import Link from "next/link";
import { Mark } from "@/components/brand/logo";

export default function NotFound() {
  return (
    <main id="main" className="on-dark grain flex min-h-dvh flex-col items-center justify-center bg-obsidian px-6 text-center text-on-dark">
      <Mark size={36} className="text-brass" />
      <h1 className="mt-8 font-display text-[clamp(2.4rem,6vw,4rem)] leading-tight">No evidence at this address.</h1>
      <p className="mt-4 max-w-md text-body text-on-dark-muted">
        The page you asked for does not exist, or has moved. That is a finding about this URL, not about you.
      </p>
      <div className="mt-8 flex flex-wrap justify-center gap-3">
        <Link href="/" className="inline-flex h-11 items-center rounded-sm bg-on-dark px-5 text-ui font-medium text-obsidian hover:bg-white">
          Go to the home page
        </Link>
        <Link href="/demo" className="inline-flex h-11 items-center rounded-sm border border-rule-dark-strong px-5 text-ui text-on-dark hover:border-on-dark-muted">
          Explore the demo
        </Link>
      </div>
    </main>
  );
}
