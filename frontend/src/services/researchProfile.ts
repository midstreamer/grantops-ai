import type { ResearchProfileRead } from "../types/researchProfile";

export type ResearchProfileUpdatePayload = {
  researcher_name?: string;
  title?: string | null;
  institution?: string | null;
  primary_research_focus?: string | null;
  research_domains?: string[];
  methods?: string[];
  target_funders?: string[];
  preferred_outputs?: string[];
  keywords?: string[];
};

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") || "http://localhost:8000";

export async function fetchResearchProfile(): Promise<ResearchProfileRead> {
  const response = await fetch(`${API_BASE_URL}/api/research-profile`);
  if (!response.ok) {
    throw new Error(`Failed to fetch research profile (${response.status})`);
  }
  return (await response.json()) as ResearchProfileRead;
}

export async function updateResearchProfile(
  id: number,
  payload: ResearchProfileUpdatePayload,
): Promise<ResearchProfileRead> {
  const response = await fetch(`${API_BASE_URL}/api/research-profile/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Failed to update research profile (${response.status})`);
  }

  return (await response.json()) as ResearchProfileRead;
}

