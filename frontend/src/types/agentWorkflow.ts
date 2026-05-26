export type WorkflowStep = {
  step: string;
  status: string;
  message: string;
  data: Record<string, unknown>;
};

export type DiscoveryWorkflowResponse = {
  query: string;
  rows: number;
  status: string;
  steps: WorkflowStep[];
  profile: Record<string, unknown>;
  opportunities_saved: number;
  opportunities_scored: number;
  top_opportunities: Array<{
    id: number;
    title: string;
    agency?: string | null;
    fit_score?: number | null;
    recommendation?: string | null;
    deadline?: string | null;
    fit_summary?: string | null;
  }>;
  literature: Array<Record<string, unknown>>;
  ai_summaries: Array<Record<string, unknown>>;
};

export type DiscoveryWorkflowRequest = {
  query: string;
  rows: number;
};
