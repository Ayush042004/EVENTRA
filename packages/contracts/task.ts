import { TaskStatus, DependencyType } from "./enums";

export interface Task {
  id: string;
  eventId: string;
  title: string;
  description: string;
  status: TaskStatus;
  plannedStart: string;
  plannedEnd: string;
  actualStart?: string;
  actualEnd?: string;
  durationMinutes: number;
  slackMinutes: number;
  isCriticalPath: boolean;
}

export interface TaskDependency {
  id: string;
  eventId: string;
  predecessorId: string;
  successorId: string;
  dependencyType: DependencyType;
  lagMinutes: number;
}
