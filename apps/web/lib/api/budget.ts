import { apiClient } from "./client";
import type {
  BudgetSummaryResponse,
  BudgetValidationResponse,
} from "../../types/api";

export async function getBudgetSummary(
  eventId: string
): Promise<BudgetSummaryResponse> {
  return apiClient.get<BudgetSummaryResponse>(`/events/${eventId}/budget/summary`);
}

export async function validateBudget(
  eventId: string
): Promise<BudgetValidationResponse> {
  return apiClient.get<BudgetValidationResponse>(`/events/${eventId}/budget/validate`);
}
