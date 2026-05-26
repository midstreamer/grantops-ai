import type { LiteratureItemRead } from "../types/literature";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") || "http://localhost:8000";

export async function getOpportunityLiterature(
  opportunityId: number,
): Promise<LiteratureItemRead[]> {
  const response = await fetch(`${API_BASE_URL}/api/opportunities/${opportunityId}/literature`);
  if (!response.ok) {
    throw new Error(`Failed to load literature (${response.status})`);
  }
  return (await response.json()) as LiteratureItemRead[];
}

export async function findSupportingLiterature(
  opportunityId: number,
): Promise<LiteratureItemRead[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/opportunities/${opportunityId}/literature`,
    { method: "POST" },
  );
  if (!response.ok) {
    throw new Error(`Failed to find literature (${response.status})`);
  }
  return (await response.json()) as LiteratureItemRead[];
}

export function literatureDoiUrl(doi: string | null, url: string | null): string | null {
  if (url) return url;
  if (!doi) return null;
  if (doi.startsWith("http")) return doi;
  return `https://doi.org/${doi}`;
}
