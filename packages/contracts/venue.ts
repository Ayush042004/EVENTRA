export interface Venue {
  id: string;
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  maxCapacity: number;
  hourlyRate: number;
  facilities: string[];
  zones?: Record<string, unknown>[];
  availabilityCalendar?: Record<string, unknown>;
  distanceKm?: number;
  estimatedTransitMinutes?: number;
}

export interface VenueSearchFilter {
  minCapacity?: number;
  maxHourlyRate?: number;
  requiredFacilities?: string[];
  maxDistanceKm?: number;
  latitude?: number;
  longitude?: number;
}
