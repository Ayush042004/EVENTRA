import { apiClient } from "./client";
import type { EventPlan } from "../../types/api";

export async function generatePlan(eventId: string): Promise<EventPlan> {
  return apiClient.post<EventPlan>(`/events/${eventId}/plan`);
}

export async function getPlan(eventId: string): Promise<EventPlan> {
  return apiClient.get<EventPlan>(`/events/${eventId}/plan`);
}
