import { apiClient } from "./client";
import type { ScheduleResponse } from "../../types/api";

export async function computeSchedule(eventId: string): Promise<ScheduleResponse> {
  return apiClient.post<ScheduleResponse>(`/events/${eventId}/schedule/compute`);
}

export async function getSchedule(eventId: string): Promise<ScheduleResponse> {
  return apiClient.get<ScheduleResponse>(`/events/${eventId}/schedule`);
}
