import { apiClient } from "./client";
import type {
  VerificationListResponse,
  VerificationResultResponse,
} from "../../types/api";

export async function verifyAction(
  eventId: string,
  actionId: string
): Promise<VerificationResultResponse> {
  return apiClient.post<VerificationResultResponse>(
    `/events/${eventId}/actions/${actionId}/verify`
  );
}

export async function listVerifications(
  eventId: string,
  params: { status?: string } = {}
): Promise<VerificationListResponse> {
  return apiClient.get<VerificationListResponse>(
    `/events/${eventId}/verifications`,
    { params }
  );
}

export async function getVerification(
  eventId: string,
  verificationId: string
): Promise<VerificationResultResponse> {
  return apiClient.get<VerificationResultResponse>(
    `/events/${eventId}/verifications/${verificationId}`
  );
}

export async function reverify(
  eventId: string,
  verificationId: string,
  reason: string = "Operator-initiated re-verification"
): Promise<VerificationResultResponse> {
  return apiClient.post<VerificationResultResponse>(
    `/events/${eventId}/verifications/${verificationId}/reverify`,
    { reason }
  );
}
