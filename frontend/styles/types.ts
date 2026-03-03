export type SourceItem = {
  title: string;
  url: string;
  source: string;
  published_at?: string | null;
};

export type Report = {
  report_id: string;
  headline: string;
  metadata: string;
  tldr: string[];
  sections: Record<string, string>;
  implications: string;
  sources: SourceItem[];
};
