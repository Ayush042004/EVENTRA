import { EventStatus, ObjectivePriority } from "./enums";

export interface EventRequirement {
  id: string;
  eventId: string;
  category: string;
  key: string;
  value: Record<string, unknown>;
  isMandatory: boolean;
}

export interface EventConstraint {
  id: string;
  eventId: string;
  constraintType: string;
  parameters: Record<string, unknown>;
}

export interface EventObjective {
  id: string;
  eventId: string;
  title: string;
  priority: ObjectivePriority;
  isThreatened: boolean;
}

export interface Event {
  id: string;
  title: string;
  description: string;
  status: EventStatus;
  startTime: string;
  endTime: string;
  guestCount: number; // Aggregate requirement, NOT attendee list
  totalBudget: number;
  currency: string;
  venueId?: string;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
}

export interface CreateEventRequest {
  title: string;
  description?: string;
  startTime: string;
  endTime: string;
  guestCount: number;
  totalBudget: number;
  currency?: string;
}
