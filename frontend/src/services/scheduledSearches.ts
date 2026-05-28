import type {
  ScheduledSearchCreate,
  ScheduledSearchRead,
  ScheduledSearchUpdate,
} from "../types/scheduledSearch";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") || "http://localhost:8000";

async function parseError(response: Response, fallback: string): Promise<never> {
  const body = (await response.json().catch(() => null)) as { detail?: string } | null;
  throw new Error(body?.detail || `${fallback} (${response.status})`);
}

export async function listScheduledSearches(): Promise<ScheduledSearchRead[]> {
  const response = await fetch(`${API_BASE_URL}/api/scheduled-searches`);
  if (!response.ok) await parseError(response, "Failed to load scheduled searches");
  return (await response.json()) as ScheduledSearchRead[];
}

export async function createScheduledSearch(
  payload: ScheduledSearchCreate,
): Promise<ScheduledSearchRead> {
  const response = await fetch(`${API_BASE_URL}/api/scheduled-searches`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) await parseError(response, "Failed to create scheduled search");
  return (await response.json()) as ScheduledSearchRead;
}

export async function updateScheduledSearch(
  id: number,
  payload: ScheduledSearchUpdate,
): Promise<ScheduledSearchRead> {
  const response = await fetch(`${API_BASE_URL}/api/scheduled-searches/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) await parseError(response, "Failed to update scheduled search");
  return (await response.json()) as ScheduledSearchRead;
}

export async function deleteScheduledSearch(id: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/scheduled-searches/${id}`, {
    method: "DELETE",
  });
  if (!response.ok) await parseError(response, "Failed to delete scheduled search");
}

export async function runScheduledSearchNow(id: number): Promise<{
  status: string;
  report_id: number;
  title: string;
}> {
  const response = await fetch(`${API_BASE_URL}/api/scheduled-searches/${id}/run-now`, {
    method: "POST",
  });
  if (!response.ok) await parseError(response, "Failed to run scheduled search");
  return (await response.json()) as { status: string; report_id: number; title: string };
}
