import { apiClient } from "./client";
import type {
  ActivityListResponse,
  AuditListResponse,
  DecisionTraceResponse,
  StateHistoryResponse,
} from "../../types/api";

export async function getAuditTrail(
  eventId: string,
  params: { action_type?: string; limit?: number } = {}
): Promise<AuditListResponse> {
  return apiClient.get<AuditListResponse>(`/events/${eventId}/audit`, { params });
}

export async function getActivityFeed(
  eventId: string,
  limit: number = 50
): Promise<ActivityListResponse> {
  return apiClient.get<ActivityListResponse>(`/events/${eventId}/activity`, {
    params: { limit },
  });
}

export async function getDecisionTraces(
  eventId: string,
  params: { verification_id?: string; limit?: number } = {}
): Promise<DecisionTraceResponse[]> {
  return apiClient.get<DecisionTraceResponse[]>(
    `/events/${eventId}/decision-trace`,
    { params }
  );
}

export async function getStateHistory(
  eventId: string,
  params: { entity_type?: string; limit?: number } = {}
): Promise<StateHistoryResponse> {
  return apiClient.get<StateHistoryResponse>(`/events/${eventId}/state-history`, {
    params,
  });
}
