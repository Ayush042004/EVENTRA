import { apiClient } from "./client";
import type {
  AgentRunRequest,
  AgentRunResponse,
} from "../../types/api";

export async function runOperationsAgent(
  eventId: string,
  payload: AgentRunRequest
): Promise<AgentRunResponse> {
  return apiClient.post<AgentRunResponse>(
    `/agent/events/${eventId}/run`,
    payload
  );
}
