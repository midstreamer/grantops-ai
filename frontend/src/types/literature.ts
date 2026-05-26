export interface LiteratureItemRead {
  id: number;
  opportunity_id: number | null;
  source: string;
  source_id: string;
  title: string;
  authors: string[];
  publication_year: number | null;
  venue: string | null;
  doi: string | null;
  url: string | null;
  abstract: string | null;
  cited_by_count: number | null;
  raw_data: Record<string, unknown>;
  created_at: string;
}
