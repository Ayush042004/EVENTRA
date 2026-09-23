import { apiClient } from "./client";
import type {
  ActionSubmissionResponse,
} from "../../types/api";

export interface ActionPayload {
  action_id?: string;
  action_type: string;
  target_type: string;
  target_id?: string;
  payload?: Record<string, unknown>;
}

export async function submitAction(
  eventId: string,
  payload: ActionPayload
): Promise<ActionSubmissionResponse> {
  return apiClient.post<ActionSubmissionResponse>(
    `/events/${eventId}/actions`,
    payload
  );
}

export async function executeRecoveryOption(
  eventId: string,
  recoveryOptionId: string,
  actionId?: string
): Promise<ActionSubmissionResponse> {
  return apiClient.post<ActionSubmissionResponse>(
    `/events/${eventId}/actions/execute-recovery`,
    {
      recovery_option_id: recoveryOptionId,
      action_id: actionId,
    }
  );
}
