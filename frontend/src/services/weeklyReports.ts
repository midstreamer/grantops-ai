import type { WeeklyReportRead } from "../types/weeklyReport";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") || "http://localhost:8000";

export async function listWeeklyReports(): Promise<WeeklyReportRead[]> {
  const response = await fetch(`${API_BASE_URL}/api/weekly-reports`);
  if (!response.ok) {
    throw new Error(`Failed to load weekly reports (${response.status})`);
  }
  return (await response.json()) as WeeklyReportRead[];
}
