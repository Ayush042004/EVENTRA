import { apiClient } from "./client";
import type {
  IncidentCreate,
  IncidentResponse,
  IncidentListResponse,
  ImpactResultResponse,
  RiskResultResponse,
} from "../../types/api";

export async function createIncident(
  eventId: string,
  payload: IncidentCreate
): Promise<IncidentResponse> {
  return apiClient.post<IncidentResponse>(`/events/${eventId}/incidents`, payload);
}

export async function listIncidents(
  eventId: string,
  params: { status?: string; incident_type?: string; limit?: number; offset?: number } = {}
): Promise<IncidentListResponse> {
  return apiClient.get<IncidentListResponse>(`/events/${eventId}/incidents`, { params });
}

export async function getIncident(
  eventId: string,
  incidentId: string
): Promise<IncidentResponse> {
  return apiClient.get<IncidentResponse>(`/events/${eventId}/incidents/${incidentId}`);
}

export async function getIncidentImpact(
  eventId: string,
  incidentId: string
): Promise<ImpactResultResponse> {
  return apiClient.get<ImpactResultResponse>(
    `/events/${eventId}/incidents/${incidentId}/impact`
  );
}

export async function getIncidentRisk(
  eventId: string,
  incidentId: string
): Promise<RiskResultResponse> {
  return apiClient.get<RiskResultResponse>(
    `/events/${eventId}/incidents/${incidentId}/risk`
  );
}

export async function recalculateIncident(
  eventId: string,
  incidentId: string
): Promise<IncidentResponse> {
  return apiClient.post<IncidentResponse>(
    `/events/${eventId}/incidents/${incidentId}/recalculate`
  );
}

export async function resolveIncident(
  eventId: string,
  incidentId: string,
  resolutionNotes?: string
): Promise<IncidentResponse> {
  return apiClient.post<IncidentResponse>(
    `/events/${eventId}/incidents/${incidentId}/resolve`,
    { resolution_notes: resolutionNotes }
  );
}
