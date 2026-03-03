type Props = {
  text: string;
};

export default function MetadataLine({ text }: Props) {
  return (
    <p className="font-ui text-[0.78rem] uppercase tracking-[0.15em] text-muted">{text}</p>
  );
}
