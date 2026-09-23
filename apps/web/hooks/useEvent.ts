"use client";

import { useState, useEffect, useCallback } from "react";
import { getEvent, getEventSpecification } from "../lib/api/events";
import type { EventResponse, EventSpecification } from "../types/api";

export function useEvent(eventId: string | null) {
  const [event, setEvent] = useState<EventResponse | null>(null);
  const [specification, setSpecification] = useState<EventSpecification | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchEventData = useCallback(async () => {
    if (!eventId) return;
    try {
      const ev = await getEvent(eventId);
      setEvent(ev);
      try {
        const spec = await getEventSpecification(eventId);
        setSpecification(spec);
      } catch {
        // Spec may not exist yet if only draft
      }
      setError(null);
    } catch (err: any) {
      setError(err?.message || "Failed to load event");
    } finally {
      setIsLoading(false);
    }
  }, [eventId]);

  useEffect(() => {
    if (!eventId) return;
    setIsLoading(true);
    fetchEventData();
  }, [eventId, fetchEventData]);

  return {
    event,
    specification,
    isLoading,
    error,
    refresh: fetchEventData,
  };
}
