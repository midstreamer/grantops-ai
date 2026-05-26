export interface ResearchProfileRead {
  id: number;
  researcher_name: string;
  title: string | null;
  institution: string | null;
  primary_research_focus: string;
  research_domains: string[];
  methods: string[];
  target_funders: string[];
  preferred_outputs: string[];
  keywords: string[];
  created_at: string; // ISO datetime
  updated_at: string; // ISO datetime
}

