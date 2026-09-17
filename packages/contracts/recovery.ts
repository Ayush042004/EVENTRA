import { RecoveryStrategyType } from "./enums";

export interface RecoveryOption {
  id: string;
  incidentId: string;
  strategyType: RecoveryStrategyType;
  title: string;
  description: string;
  actions: Record<string, unknown>[];
  costImpact: number;
  delayImpactMinutes: number;
  feasibilityScore: number;
  isSelected: boolean;
}
