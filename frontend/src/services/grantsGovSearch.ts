import type { GrantOpportunityRead } from "../types/opportunity";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") || "http://localhost:8000";

export async function searchGrantsGov(
  query: string,
  rows: number,
): Promise<GrantOpportunityRead[]> {
  const response = await fetch(`${API_BASE_URL}/api/search/grants-gov`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, rows }),
  });

  if (!response.ok) {
    throw new Error(`Grants.gov search failed (${response.status})`);
  }

  return (await response.json()) as GrantOpportunityRead[];
}

