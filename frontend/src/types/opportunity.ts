export type OpportunityRecommendation = "pursue" | "monitor" | "decline" | "unreviewed";

export type OpportunityStatus =
  | "new"
  | "review"
  | "pursuing"
  | "drafting"
  | "submitted"
  | "declined";

export interface GrantOpportunityRead {
  id: number;
  source: string;
  source_id: string | null;
  title: string;
  agency: string | null;
  program: string | null;
  description: string | null;
  eligibility: string | null;
  award_ceiling: number | null;
  award_floor: number | null;
  deadline: string | null; // yyyy-mm-dd
  posted_date: string | null; // yyyy-mm-dd
  opportunity_status: string | null;
  url: string | null;
  raw_data: Record<string, unknown>;
  fit_score: number | null;
  fit_summary: string | null;
  recommendation: OpportunityRecommendation;
  status: OpportunityStatus;
  next_action: string | null;
  notes: string | null;
  created_at: string; // ISO datetime
  updated_at: string; // ISO datetime
}

export interface OpportunityScoreResult {
  fit_score: number;
  recommendation: OpportunityRecommendation;
  fit_summary: string;
  matched_keywords: string[];
  concerns: string[];
  recommended_next_action: string;
  breakdown?: FitScoreBreakdown;
}

export interface GrantOpportunityCreate {
  source: string;
  source_id?: string | null;
  title: string;
  agency?: string | null;
  program?: string | null;
  description?: string | null;
  eligibility?: string | null;
  award_ceiling?: number | null;
  award_floor?: number | null;
  deadline?: string | null;
  posted_date?: string | null;
  opportunity_status?: string | null;
  url?: string | null;
  raw_data?: Record<string, unknown>;
  fit_score?: number | null;
  fit_summary?: string | null;
  recommendation?: OpportunityRecommendation;
  status?: OpportunityStatus;
  next_action?: string | null;
  notes?: string | null;
}

export type GrantOpportunityUpdate = Partial<GrantOpportunityCreate>;

export interface FitScoreBreakdown {
  topic_alignment: number;
  method_alignment: number;
  funder_relevance: number;
  eligibility_fit: number;
  deadline_feasibility: number;
  budget_fit: number;
  collaboration_potential: number;
  academic_career_value: number;
}

