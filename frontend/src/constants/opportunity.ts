import type { OpportunityRecommendation, OpportunityStatus } from "../types/opportunity";

export const RECOMMENDATION_OPTIONS: OpportunityRecommendation[] = [
  "unreviewed",
  "pursue",
  "monitor",
  "decline",
];

export const STATUS_OPTIONS: OpportunityStatus[] = [
  "new",
  "review",
  "pursuing",
  "drafting",
  "submitted",
  "declined",
];

export type SortField = "deadline" | "fit_score";
export type SortDirection = "asc" | "desc";

export function recommendationClass(value: OpportunityRecommendation): string {
  if (value === "pursue") return "recommendation-badge pursue";
  if (value === "monitor") return "recommendation-badge monitor";
  if (value === "decline") return "recommendation-badge decline";
  return "recommendation-badge unreviewed";
}

export function formatDate(value: string | null): string {
  if (!value) return "—";
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString();
}
