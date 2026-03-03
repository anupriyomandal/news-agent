import Link from "next/link";

import ArticleSection from "@/components/ArticleSection";
import Divider from "@/components/Divider";
import MetadataLine from "@/components/MetadataLine";
import TLDRBox from "@/components/TLDRBox";
import { getReport } from "@/styles/api";

export default async function ArticlePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const report = await getReport(id);

  return (
    <main className="mx-auto max-w-article px-6 pb-20 pt-14">
      <header>
        <Link href="/" className="font-ui text-xs uppercase tracking-[0.15em] text-muted underline underline-offset-4">
          Back to Search
        </Link>
        <h1 className="mt-6 font-headline text-[3rem] leading-[1.12] text-ink">{report.headline}</h1>
        <div className="mt-4">
          <MetadataLine text={report.metadata} />
        </div>
      </header>

      <Divider />
      <TLDRBox points={report.tldr} />

      {Object.entries(report.sections).map(([title, content]) => (
        <ArticleSection key={title} title={title} content={content} />
      ))}

      <section className="mb-10">
        <h2 className="font-headline text-[1.8rem] leading-tight">Implications / What Analysts Are Watching</h2>
        <p className="mt-3 font-body text-[1.07rem] leading-8">{report.implications}</p>
      </section>

      <Divider />
      <section>
        <h2 className="font-headline text-[1.8rem] leading-tight">Sources Referenced</h2>
        <ul className="mt-4 space-y-2 font-body text-[1.02rem] leading-7">
          {report.sources.map((source) => (
            <li key={source.url}>
              <a href={source.url} target="_blank" rel="noreferrer" className="underline underline-offset-4">
                {source.title}
              </a>{" "}
              <span className="text-muted">({source.source})</span>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
