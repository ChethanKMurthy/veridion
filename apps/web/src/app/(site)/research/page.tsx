import type { Metadata } from "next";
import Link from "next/link";
import { Container, Masthead } from "@/components/site/chrome";
import { ArrowRight } from "@/components/ui/icons";
import { articles } from "@/content/research";
import { date } from "@/lib/format";

export const metadata: Metadata = {
  title: "Research",
  description: "Notes on disclosure evidence, peer comparison and reporting standards from the Veridion team.",
};

export default function ResearchPage() {
  return (
    <>
      <Masthead title="Research" lead="Notes on evidence, comparison and reporting standards — written to be useful whether or not you use Veridion." />
      <Container className="py-16 lg:py-24">
        <ol className="divide-y divide-rule border-y border-rule">
          {articles.map((a) => (
            <li key={a.slug}>
              <Link href={`/research/${a.slug}`} className="group grid gap-4 py-8 md:grid-cols-[12rem_minmax(0,1fr)_auto] md:items-start">
                <span className="text-ui-sm text-ink-muted">
                  {date(a.date)}
                  <span className="block">{a.topic}</span>
                </span>
                <span>
                  <span className="block font-display text-[1.75rem] leading-tight text-ink group-hover:underline group-hover:decoration-rule-strong group-hover:underline-offset-4">
                    {a.title}
                  </span>
                  <span className="mt-3 block max-w-2xl text-body text-ink-muted">{a.summary}</span>
                </span>
                <span className="flex items-center gap-2 text-ui-sm text-ink-muted md:pt-2">
                  {a.readingTime} <ArrowRight size={14} />
                </span>
              </Link>
            </li>
          ))}
        </ol>
      </Container>
    </>
  );
}
