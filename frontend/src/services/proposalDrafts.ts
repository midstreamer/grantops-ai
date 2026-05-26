import type { ProposalDraftRead, ProposalDraftUpdate } from "../types/proposalDraft";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") || "http://localhost:8000";

async function parseError(response: Response, fallback: string): Promise<never> {
  const body = (await response.json().catch(() => null)) as { detail?: string } | null;
  throw new Error(body?.detail || `${fallback} (${response.status})`);
}

export async function listOpportunityDrafts(
  opportunityId: number,
): Promise<ProposalDraftRead[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/opportunities/${opportunityId}/drafts`,
  );
  if (!response.ok) {
    await parseError(response, "Failed to load proposal drafts");
  }
  return (await response.json()) as ProposalDraftRead[];
}

export async function generateConceptNote(
  opportunityId: number,
): Promise<ProposalDraftRead> {
  const response = await fetch(
    `${API_BASE_URL}/api/opportunities/${opportunityId}/concept-note`,
    { method: "POST" },
  );
  if (!response.ok) {
    await parseError(response, "Failed to generate concept note");
  }
  return (await response.json()) as ProposalDraftRead;
}

export async function exportProposalDraftToGoogleDoc(
  draftId: number,
): Promise<ProposalDraftRead> {
  const response = await fetch(
    `${API_BASE_URL}/api/proposal-drafts/${draftId}/export/google-doc`,
    { method: "POST" },
  );
  if (!response.ok) {
    await parseError(response, "Failed to export to Google Docs");
  }
  return (await response.json()) as ProposalDraftRead;
}

export async function updateProposalDraft(
  opportunityId: number,
  draftId: number,
  payload: ProposalDraftUpdate,
): Promise<ProposalDraftRead> {
  const response = await fetch(
    `${API_BASE_URL}/api/opportunities/${opportunityId}/drafts/${draftId}`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
  );
  if (!response.ok) {
    await parseError(response, "Failed to save draft");
  }
  return (await response.json()) as ProposalDraftRead;
}
