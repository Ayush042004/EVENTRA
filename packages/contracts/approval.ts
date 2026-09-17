import { ActionImpactLevel, ApprovalStatus } from "./enums";

export interface Approval {
  id: string;
  eventId: string;
  recoveryId?: string;
  actionType: string;
  impactLevel: ActionImpactLevel;
  requestedBy: "AGENT" | "USER";
  approverId?: string;
  status: ApprovalStatus;
  description: string;
  payload: Record<string, unknown>;
  createdAt: string;
  resolvedAt?: string;
}

export interface ResolveApprovalRequest {
  status: ApprovalStatus.APPROVED | ApprovalStatus.REJECTED;
  notes?: string;
}
