import type { OpportunityAISummary } from "../types/aiSummary";
import type {
  GrantOpportunityCreate,
  GrantOpportunityRead,
  GrantOpportunityUpdate,
  OpportunityScoreResult,
} from "../types/opportunity";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") || "http://localhost:8000";

export async function listOpportunities(): Promise<GrantOpportunityRead[]> {
  const response = await fetch(`${API_BASE_URL}/api/opportunities`);
  if (!response.ok) {
    throw new Error(`Failed to load opportunities (${response.status})`);
  }
  return (await response.json()) as GrantOpportunityRead[];
}

export async function createOpportunity(
  payload: GrantOpportunityCreate,
): Promise<GrantOpportunityRead> {
  const response = await fetch(`${API_BASE_URL}/api/opportunities`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(`Failed to create opportunity (${response.status})`);
  }
  return (await response.json()) as GrantOpportunityRead;
}

export async function getOpportunity(id: number): Promise<GrantOpportunityRead> {
  const response = await fetch(`${API_BASE_URL}/api/opportunities/${id}`);
  if (!response.ok) {
    throw new Error(`Failed to load opportunity (${response.status})`);
  }
  return (await response.json()) as GrantOpportunityRead;
}

export async function updateOpportunity(
  id: number,
  payload: GrantOpportunityUpdate,
): Promise<GrantOpportunityRead> {
  const response = await fetch(`${API_BASE_URL}/api/opportunities/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(`Failed to update opportunity (${response.status})`);
  }
  return (await response.json()) as GrantOpportunityRead;
}

export async function deleteOpportunity(id: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/opportunities/${id}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new Error(`Failed to delete opportunity (${response.status})`);
  }
}

export async function generateAiSummary(id: number): Promise<OpportunityAISummary> {
  const response = await fetch(`${API_BASE_URL}/api/opportunities/${id}/ai-summary`, {
    method: "POST",
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string } | null;
    const message = body?.detail || `Failed to generate AI summary (${response.status})`;
    throw new Error(message);
  }
  return (await response.json()) as OpportunityAISummary;
}

export async function scoreOpportunity(
  id: number,
): Promise<{ opportunity: GrantOpportunityRead; score: OpportunityScoreResult }> {
  const response = await fetch(`${API_BASE_URL}/api/opportunities/${id}/score`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error(`Failed to score opportunity (${response.status})`);
  }
  return (await response.json()) as {
    opportunity: GrantOpportunityRead;
    score: OpportunityScoreResult;
  };
}

export type GoogleSheetsExportResult = {
  spreadsheet_id: string;
  worksheet: string;
  total_rows: number;
  rows_updated: number;
  rows_appended: number;
};

export async function exportOpportunitiesToGoogleSheets(): Promise<GoogleSheetsExportResult> {
  const response = await fetch(`${API_BASE_URL}/api/export/google-sheets`, {
    method: "POST",
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string } | null;
    const message =
      body?.detail || `Failed to export to Google Sheets (${response.status})`;
    throw new Error(message);
  }
  return (await response.json()) as GoogleSheetsExportResult;
}

export async function downloadOpportunitiesCsv(): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/export/opportunities.csv`);
  if (!response.ok) {
    throw new Error(`Failed to export opportunities (${response.status})`);
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "grantops-opportunities.csv";
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export async function scoreAllOpportunities(): Promise<{
  count: number;
  results: Array<{ opportunity_id: number; fit_score: number; recommendation: string }>;
}> {
  const response = await fetch(`${API_BASE_URL}/api/opportunities/score-all`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error(`Failed to score all opportunities (${response.status})`);
  }
  return (await response.json()) as {
    count: number;
    results: Array<{ opportunity_id: number; fit_score: number; recommendation: string }>;
  };
}

