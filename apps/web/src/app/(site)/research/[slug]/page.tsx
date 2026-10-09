import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { Container, CtaBand } from "@/components/site/chrome";
import { ArrowLeft } from "@/components/ui/icons";
import { articleBySlug, articles } from "@/content/research";
import { date } from "@/lib/format";

export function generateStaticParams() {
  return articles.map((a) => ({ slug: a.slug }));
}

export async function generateMetadata({ params }: PageProps<"/research/[slug]">): Promise<Metadata> {
  const { slug } = await params;
  const article = articleBySlug(slug);
  return article ? { title: article.title, description: article.summary } : { title: "Research" };
}

export default function ArticlePage({ params }: PageProps<"/research/[slug]">) {
  return (
    <Suspense fallback={<div className="min-h-[60vh] bg-obsidian" aria-busy="true" />}>
      <Article params={params} />
    </Suspense>
  );
}

async function Article({ params }: { params: PageProps<"/research/[slug]">["params"] }) {
  const { slug } = await params;
  const article = articleBySlug(slug);
  if (!article) notFound();
  return (
    <>
      <section className="on-dark grain bg-obsidian text-on-dark">
        <Container className="pb-16 pt-14 lg:pb-20 lg:pt-20">
          <Link href="/research" className="inline-flex items-center gap-1.5 text-ui-sm text-on-dark-muted hover:text-on-dark">
            <ArrowLeft size={14} /> Research
          </Link>
          <h1 className="mt-6 max-w-4xl font-display text-[clamp(2.2rem,4.6vw,3.8rem)] leading-[1.06] tracking-[-0.015em]">{article.title}</h1>
          <p className="mt-6 max-w-2xl text-lead text-on-dark-muted">{article.summary}</p>
          <p className="mt-6 text-ui-sm text-on-dark-muted">
            {date(article.date)} · {article.topic} · {article.readingTime} · Veridion research
          </p>
        </Container>
      </section>
      <Container className="py-14 lg:py-20">
        <article className="prose-veridion mx-auto">
          {article.body}
          {article.sources?.length ? (
            <>
              <h2>Sources</h2>
              <ul>
                {article.sources.map((s) => (
                  <li key={s.url}>
                    <a href={s.url} target="_blank" rel="noreferrer">{s.label}</a>
                  </li>
                ))}
              </ul>
            </>
          ) : null}
        </article>
      </Container>
      <CtaBand title="See these ideas in the product." />
    </>
  );
}
