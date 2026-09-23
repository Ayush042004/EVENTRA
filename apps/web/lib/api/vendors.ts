import { apiClient } from "./client";
import type {
  PaginatedVendorsResponse,
  VendorResponse,
  VendorAssignmentResponse,
  VendorAssignmentCreate,
  ProviderAvailabilityResult,
  CategoryValidationResult,
} from "../../types/api";

export interface VendorSearchParams {
  [key: string]: string | number | boolean | null | undefined;
  category?: string;
  city?: string;
  max_base_cost?: number;
  limit?: number;
  offset?: number;
}

export async function searchVendors(
  params: VendorSearchParams = {}
): Promise<PaginatedVendorsResponse> {
  return apiClient.get<PaginatedVendorsResponse>("/vendors", { params });
}

export async function getVendor(vendorId: string): Promise<VendorResponse> {
  return apiClient.get<VendorResponse>(`/vendors/${vendorId}`);
}

export async function getAssignmentsForEvent(
  eventId: string
): Promise<VendorAssignmentResponse[]> {
  return apiClient.get<VendorAssignmentResponse[]>(
    `/vendors/assignments/event/${eventId}`
  );
}

export const getEventAssignments = getAssignmentsForEvent;

export async function createAssignment(
  payload: VendorAssignmentCreate
): Promise<VendorAssignmentResponse> {
  return apiClient.post<VendorAssignmentResponse>(
    "/vendors/assignments",
    payload
  );
}

export async function checkProviderAvailability(
  vendorId: string,
  startDatetime: string,
  endDatetime: string
): Promise<ProviderAvailabilityResult> {
  return apiClient.get<ProviderAvailabilityResult>(
    `/vendors/${vendorId}/availability`,
    {
      params: {
        start_datetime: startDatetime,
        end_datetime: endDatetime,
      },
    }
  );
}

export async function validateCategoryForDomain(
  domain: string,
  category: string
): Promise<CategoryValidationResult> {
  return apiClient.get<CategoryValidationResult>("/vendors/categories/validate", {
    params: { domain, category },
  });
}
