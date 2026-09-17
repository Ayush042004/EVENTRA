import { IncidentSeverity, IncidentStatus } from "./enums";

export interface Incident {
  id: string;
  eventId: string;
  title: string;
  description: string;
  reportedBy?: string;
  severity: IncidentSeverity;
  status: IncidentStatus;
  affectedTaskIds: string[];
  createdAt: string;
  resolvedAt?: string;
}

export interface ReportIncidentRequest {
  eventId: string;
  title: string;
  description: string;
  severity?: IncidentSeverity;
  affectedTaskIds?: string[];
}
