import Link from "next/link";
import { Mark, Wordmark } from "@/components/brand/logo";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="grid min-h-dvh lg:grid-cols-[minmax(0,1fr)_minmax(0,0.9fr)]">
      <main id="main" className="flex flex-col px-6 py-8 sm:px-12">
        <Link href="/" className="text-ink" aria-label="Veridion home">
          <Wordmark />
        </Link>
        <div className="mx-auto flex w-full max-w-sm flex-1 flex-col justify-center py-12">{children}</div>
        <p className="text-meta text-ink-muted">
          <Link href="/trust/security" className="hover:text-ink">Security</Link>
          <span className="mx-2">·</span>
          <Link href="/legal/privacy-notice" className="hover:text-ink">Privacy</Link>
          <span className="mx-2">·</span>
          <Link href="/contact" className="hover:text-ink">Contact</Link>
        </p>
      </main>
      <aside className="on-dark grain relative hidden overflow-hidden bg-obsidian text-on-dark lg:flex lg:flex-col lg:justify-between lg:p-14">
        <Mark size={40} className="text-brass" />
        <div className="max-w-md">
          <p className="font-display text-[2.4rem] leading-[1.1] tracking-[-0.01em]">
            Every finding, one click from the page it came from.
          </p>
          <p className="mt-5 text-ui leading-relaxed text-on-dark-muted">
            Veridion links each conclusion to the passage, page and requirement version behind it — and says plainly when the
            evidence is missing, partial or in conflict.
          </p>
        </div>
        <p className="text-meta text-on-dark-muted">Company intelligence, grounded in evidence.</p>
      </aside>
    </div>
  );
}
