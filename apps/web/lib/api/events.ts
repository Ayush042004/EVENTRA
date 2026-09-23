import { apiClient } from "./client";
import type {
  EventCreate,
  EventResponse,
  EventSpecification,
  EventSpecificationPreviewRequest,
} from "../../types/api";

export async function listEvents(): Promise<EventResponse[]> {
  try {
    return await apiClient.get<EventResponse[]>("/events");
  } catch {
    return [];
  }
}

export async function getEvent(eventId: string): Promise<EventResponse> {
  return apiClient.get<EventResponse>(`/events/${eventId}`);
}

export async function createEvent(payload: EventCreate): Promise<EventResponse> {
  return apiClient.post<EventResponse>("/events", payload);
}

export async function previewEventSpecification(
  payload: EventSpecificationPreviewRequest
): Promise<EventSpecification> {
  return apiClient.post<EventSpecification>("/events/specification/preview", payload);
}

export async function getEventSpecification(
  eventId: string
): Promise<EventSpecification> {
  return apiClient.get<EventSpecification>(`/events/${eventId}/specification`);
}

export async function getEventMembers(eventId: string): Promise<any[]> {
  return apiClient.get<any[]>(`/events/${eventId}/members`);
}
