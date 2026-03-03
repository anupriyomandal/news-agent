type Props = {
  title: string;
  content: string;
};

export default function ArticleSection({ title, content }: Props) {
  return (
    <section className="mb-10">
      <h3 className="font-headline text-[1.8rem] leading-tight text-ink">{title}</h3>
      <p className="mt-3 whitespace-pre-line font-body text-[1.07rem] leading-8 text-ink">{content}</p>
    </section>
  );
}
