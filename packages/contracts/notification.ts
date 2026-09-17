import { NotificationChannel } from "./enums";

export interface Notification {
  id: string;
  eventId: string;
  recipientUserId: string;
  channel: NotificationChannel;
  title: string;
  message: string;
  isUrgent: boolean;
  sentAt: string;
  readAt?: string;
}
