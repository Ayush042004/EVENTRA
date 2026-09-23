"use client";

import { useState, useEffect, useCallback } from "react";
import { getLiveState, goLive as apiGoLive, concludeEvent as apiConclude, updateTaskStatus as apiUpdateTask } from "../lib/api/live";
import type { EventLiveState } from "../types/api";

export function useLiveState(eventId: string | null) {
  const [liveState, setLiveState] = useState<EventLiveState | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchLiveState = useCallback(async () => {
    if (!eventId) return;
    try {
      const data = await getLiveState(eventId);
      setLiveState(data);
      setError(null);
    } catch (err: any) {
      setError(err?.message || "Failed to load live state");
    } finally {
      setIsLoading(false);
    }
  }, [eventId]);

  useEffect(() => {
    if (!eventId) return;
    setIsLoading(true);
    fetchLiveState();

    // Periodic telemetry refresh every 5 seconds
    const interval = setInterval(fetchLiveState, 5000);
    return () => clearInterval(interval);
  }, [eventId, fetchLiveState]);

  const goLive = async (reason?: string) => {
    if (!eventId) return;
    setIsLoading(true);
    try {
      const res = await apiGoLive(eventId, reason);
      setLiveState(res);
      return res;
    } finally {
      setIsLoading(false);
    }
  };

  const conclude = async (reason?: string) => {
    if (!eventId) return;
    setIsLoading(true);
    try {
      const res = await apiConclude(eventId, reason);
      setLiveState(res);
      return res;
    } finally {
      setIsLoading(false);
    }
  };

  const updateTask = async (taskId: string, status: string, actualStart?: string, actualEnd?: string) => {
    if (!eventId) return;
    await apiUpdateTask(eventId, taskId, status, actualStart, actualEnd);
    await fetchLiveState();
  };

  return {
    liveState,
    isLoading,
    error,
    refresh: fetchLiveState,
    goLive,
    conclude,
    updateTask,
  };
}
