import { apiClient } from "./client";

export interface ProviderEngagementPayload {
  target_amount?: number;
  max_approved_amount?: number;
  currency?: string;
  required_coverage_start?: string;
  required_coverage_end?: string;
}

export interface SimulateProviderPayload {
  scenario: "ACCEPT" | "COUNTER" | "DECLINE" | "NO_RESPONSE";
  quoted_amount?: number;
  counter_coverage_start?: string;
  counter_coverage_end?: string;
  advance_required?: boolean;
  provider_count?: number;
  message?: string;
}

export interface NegotiationResult {
  assignment_id: string;
  negotiation_status: string;
  action?: string;
  message?: string;
  offer?: Record<string, unknown>;
  quoted_amount?: number;
  target_amount?: number;
  max_approved_amount?: number;
  counter_offer_amount?: number;
  round?: number;
  budget_validation?: Record<string, unknown>;
  is_simulation?: boolean;
  approval_id?: string;
  approval_status?: string;
  success?: boolean;
  agreed_cost?: number;
  vendor_name?: string;
  category?: string;
}

export interface NegotiationConversation {
  assignment: Record<string, unknown>;
  vendor?: Record<string, unknown>;
  messages: Array<Record<string, unknown>>;
  budget_validation?: Record<string, unknown>;
  requirement_validation?: Record<string, unknown>;
}

export async function engageProvider(
  assignmentId: string,
  payload: ProviderEngagementPayload
): Promise<NegotiationResult> {
  return apiClient.post<NegotiationResult>(
    `/vendors/assignments/${assignmentId}/engage`,
    payload
  );
}

export async function simulateProviderResponse(
  assignmentId: string,
  payload: SimulateProviderPayload
): Promise<NegotiationResult> {
  return apiClient.post<NegotiationResult>(
    `/vendors/assignments/${assignmentId}/simulate`,
    payload
  );
}

export async function negotiateWithProvider(
  assignmentId: string
): Promise<NegotiationResult> {
  return apiClient.post<NegotiationResult>(
    `/vendors/assignments/${assignmentId}/negotiate`,
    {}
  );
}

export async function requestEngagementApproval(
  assignmentId: string
): Promise<NegotiationResult> {
  return apiClient.post<NegotiationResult>(
    `/vendors/assignments/${assignmentId}/request-approval`,
    {}
  );
}

export async function confirmProviderEngagement(
  assignmentId: string
): Promise<NegotiationResult> {
  return apiClient.post<NegotiationResult>(
    `/vendors/assignments/${assignmentId}/confirm`,
    {}
  );
}

export async function getNegotiationConversation(
  assignmentId: string
): Promise<NegotiationConversation> {
  return apiClient.get<NegotiationConversation>(
    `/vendors/assignments/${assignmentId}/conversation`
  );
}
