type Props = {
  points: string[];
};

export default function TLDRBox({ points }: Props) {
  return (
    <section className="my-8 border border-rule bg-[#efefeb] px-5 py-4 shadow-subtle">
      <h2 className="font-ui text-xs uppercase tracking-[0.2em] text-muted">TL;DR</h2>
      <ul className="mt-3 list-disc space-y-2 pl-5 font-body text-[1.03rem] leading-7 text-ink">
        {points.map((point, idx) => (
          <li key={`${point.slice(0, 24)}-${idx}`}>{point}</li>
        ))}
      </ul>
    </section>
  );
}
