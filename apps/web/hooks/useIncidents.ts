"use client";

import { useState, useEffect, useCallback } from "react";
import {
  listIncidents,
  createIncident as apiCreateIncident,
  recalculateIncident as apiRecalculate,
  resolveIncident as apiResolve,
} from "../lib/api/incidents";
import type { IncidentResponse, IncidentCreate } from "../types/api";

export function useIncidents(eventId: string | null) {
  const [incidents, setIncidents] = useState<IncidentResponse[]>([]);
  const [selectedIncident, setSelectedIncident] = useState<IncidentResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchIncidents = useCallback(async () => {
    if (!eventId) return;
    try {
      const res = await listIncidents(eventId);
      setIncidents(res.items || []);
      if (res.items?.length > 0 && !selectedIncident) {
        setSelectedIncident(res.items[0]);
      } else if (selectedIncident) {
        const updated = res.items.find((i: IncidentResponse) => i.id === selectedIncident.id);
        if (updated) setSelectedIncident(updated);
      }
      setError(null);
    } catch (err: any) {
      setError(err?.message || "Failed to load incidents");
    } finally {
      setIsLoading(false);
    }
  }, [eventId, selectedIncident]);

  useEffect(() => {
    if (!eventId) return;
    setIsLoading(true);
    fetchIncidents();
  }, [eventId, fetchIncidents]);

  const reportIncident = async (payload: IncidentCreate) => {
    if (!eventId) return;
    setIsLoading(true);
    try {
      const res = await apiCreateIncident(eventId, payload);
      await fetchIncidents();
      setSelectedIncident(res);
      return res;
    } finally {
      setIsLoading(false);
    }
  };

  const recalculate = async (incidentId: string) => {
    if (!eventId) return;
    setIsLoading(true);
    try {
      const res = await apiRecalculate(eventId, incidentId);
      setSelectedIncident(res);
      await fetchIncidents();
      return res;
    } finally {
      setIsLoading(false);
    }
  };

  const resolve = async (incidentId: string, notes?: string) => {
    if (!eventId) return;
    setIsLoading(true);
    try {
      const res = await apiResolve(eventId, incidentId, notes);
      setSelectedIncident(res);
      await fetchIncidents();
      return res;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    incidents,
    selectedIncident,
    setSelectedIncident,
    isLoading,
    error,
    refresh: fetchIncidents,
    reportIncident,
    recalculate,
    resolve,
  };
}
