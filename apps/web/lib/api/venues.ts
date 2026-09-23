import { apiClient } from "./client";
import type {
  PaginatedVenuesResponse,
  VenueResponse,
  VenueAvailabilityResult,
  VenueSuitabilityCheck,
  VenueSuitabilityResult,
} from "../../types/api";

export interface VenueSearchParams {
  [key: string]: string | number | boolean | null | undefined;
  city?: string;
  min_capacity?: number;
  max_capacity?: number;
  venue_type?: string;
  max_hourly_rate?: number;
  limit?: number;
  offset?: number;
}

export async function searchVenues(
  params: VenueSearchParams = {}
): Promise<PaginatedVenuesResponse> {
  return apiClient.get<PaginatedVenuesResponse>("/venues", { params });
}

export async function getVenue(venueId: string): Promise<VenueResponse> {
  return apiClient.get<VenueResponse>(`/venues/${venueId}`);
}

export async function checkVenueAvailability(
  venueId: string,
  startDatetime: string,
  endDatetime: string
): Promise<VenueAvailabilityResult> {
  return apiClient.get<VenueAvailabilityResult>(`/venues/${venueId}/availability`, {
    params: {
      start_datetime: startDatetime,
      end_datetime: endDatetime,
    },
  });
}

export async function checkVenueSuitability(
  venueId: string,
  payload: VenueSuitabilityCheck
): Promise<VenueSuitabilityResult> {
  return apiClient.post<VenueSuitabilityResult>(
    `/venues/${venueId}/suitability`,
    payload
  );
}

export interface VenueDiscoveryParams {
  city?: string;
  query?: string;
  latitude?: number;
  longitude?: number;
  limit?: number;
  save_to_db?: boolean;
}

export async function discoverVenues(
  payload: VenueDiscoveryParams = {}
): Promise<{ total_discovered: number; total_created: number; city: string; source: string; items: VenueResponse[] }> {
  return apiClient.post("/venues/discover", payload);
}

export async function discoverVenuesForEvent(
  eventId: string,
  payload: VenueDiscoveryParams = {}
): Promise<{ total_discovered: number; total_created: number; city: string; source: string; items: VenueResponse[] }> {
  return apiClient.post(`/events/${eventId}/venues/discover`, payload);
}

