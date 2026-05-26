import type { GrantOpportunityRead } from "./opportunity";

export interface DashboardStats {
  total_opportunities: number;
  pursue_count: number;
  monitor_count: number;
  decline_count: number;
  due_in_30_days: number;
  due_in_90_days: number;
  average_fit_score: number | null;
  top_opportunities: GrantOpportunityRead[];
}
