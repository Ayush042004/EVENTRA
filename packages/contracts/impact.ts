export interface ImpactAnalysis {
  incidentId: string;
  directlyAffectedTaskIds: string[];
  downstreamAffectedTaskIds: string[];
  totalDelayedMinutes: number;
  criticalPathDelayedMinutes: number;
  threatenedObjectiveIds: string[];
  estimatedCostVariance: number;
}
