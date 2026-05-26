import type { DashboardStats } from "../types/dashboard";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") || "http://localhost:8000";

export async function fetchDashboardStats(): Promise<DashboardStats> {
  const response = await fetch(`${API_BASE_URL}/api/dashboard/stats`);
  if (!response.ok) {
    throw new Error(`Failed to load dashboard stats (${response.status})`);
  }
  return (await response.json()) as DashboardStats;
}
