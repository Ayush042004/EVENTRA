import { apiClient } from "./client";
import type {
  NotificationItem,
  ProviderMessage,
} from "../../types/api";

export async function getIntegrationsStatus(): Promise<Record<string, unknown>> {
  return apiClient.get<Record<string, unknown>>("/integrations/status");
}

export async function getMapDistance(
  origin: string | number[] | Record<string, number>,
  destination: string | number[] | Record<string, number>
): Promise<Record<string, unknown>> {
  return apiClient.post<Record<string, unknown>>("/integrations/maps/distance", {
    origin,
    destination,
  });
}

export async function geocodeAddress(
  address: string
): Promise<Record<string, unknown>> {
  return apiClient.post<Record<string, unknown>>("/integrations/maps/geocode", {
    address,
  });
}

export async function listNotifications(
  eventId: string,
  limit: number = 50
): Promise<{ total: number; items: NotificationItem[] }> {
  return apiClient.get<{ total: number; items: NotificationItem[] }>(
    `/events/${eventId}/notifications`,
    { params: { limit } }
  );
}

export async function sendNotification(
  eventId: string,
  payload: {
    notification_type: string;
    title: string;
    message: string;
    channel?: string;
    recipient?: string;
    payload?: Record<string, unknown>;
  }
): Promise<Record<string, unknown>> {
  return apiClient.post<Record<string, unknown>>(
    `/events/${eventId}/notifications`,
    payload
  );
}

export async function getProviderMessages(
  eventId: string,
  providerId: string
): Promise<{ total: number; items: ProviderMessage[] }> {
  return apiClient.get<{ total: number; items: ProviderMessage[] }>(
    `/events/${eventId}/providers/${providerId}/messages`
  );
}

export async function sendProviderMessage(
  eventId: string,
  providerId: string,
  message: string,
  recipientContact?: string
): Promise<Record<string, unknown>> {
  return apiClient.post<Record<string, unknown>>(
    `/events/${eventId}/providers/${providerId}/messages`,
    {
      message,
      recipient_contact: recipientContact,
    }
  );
}
