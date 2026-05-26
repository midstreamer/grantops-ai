import type {
  DiscoveryWorkflowRequest,
  DiscoveryWorkflowResponse,
} from "../types/agentWorkflow";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") || "http://localhost:8000";

export async function runDiscoveryWorkflow(
  payload: DiscoveryWorkflowRequest,
): Promise<DiscoveryWorkflowResponse> {
  const response = await fetch(`${API_BASE_URL}/api/agents/discovery-workflow`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(body?.detail || `Discovery workflow failed (${response.status})`);
  }
  return (await response.json()) as DiscoveryWorkflowResponse;
}
