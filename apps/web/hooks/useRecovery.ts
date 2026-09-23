"use client";

import { useState, useEffect, useCallback } from "react";
import {
  listRecoveryOptions,
  generateRecoveryOptions as apiGenerate,
  recalculateRecoveryOptions as apiRecalculate,
} from "../lib/api/recovery";
import { executeRecoveryOption as apiExecuteRecovery } from "../lib/api/actions";
import type { RecoveryOptionResponse } from "../types/api";

export function useRecovery(eventId: string | null, incidentId: string | null) {
  const [options, setOptions] = useState<RecoveryOptionResponse[]>([]);
  const [snapshot, setSnapshot] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchOptions = useCallback(async () => {
    if (!eventId || !incidentId) return;
    try {
      const res = await listRecoveryOptions(eventId, incidentId);
      setOptions(res.items || []);
      setSnapshot(res.state_snapshot || "");
      setError(null);
    } catch (err: any) {
      // 404 or empty is fine before generation
      setOptions([]);
    } finally {
      setIsLoading(false);
    }
  }, [eventId, incidentId]);

  useEffect(() => {
    if (!eventId || !incidentId) {
      setOptions([]);
      return;
    }
    setIsLoading(true);
    fetchOptions();
  }, [eventId, incidentId, fetchOptions]);

  const generate = async () => {
    if (!eventId || !incidentId) return;
    setIsLoading(true);
    try {
      const res = await apiGenerate(eventId, incidentId);
      setOptions(res.items || []);
      setSnapshot(res.state_snapshot || "");
      setError(null);
      return res;
    } catch (err: any) {
      setError(err?.message || "Failed to generate recovery options");
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const recalculate = async () => {
    if (!eventId || !incidentId) return;
    setIsLoading(true);
    try {
      const res = await apiRecalculate(eventId, incidentId);
      setOptions(res.items || []);
      setSnapshot(res.state_snapshot || "");
      setError(null);
      return res;
    } catch (err: any) {
      setError(err?.message || "Failed to recalculate recovery options");
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const execute = async (optionId: string) => {
    if (!eventId) return;
    setIsLoading(true);
    try {
      const res = await apiExecuteRecovery(eventId, optionId);
      await fetchOptions();
      return res;
    } catch (err: any) {
      setError(err?.message || "Failed to execute recovery option");
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const hasStaleOption = options.some((opt) => opt.is_stale || opt.status === "STALE");

  return {
    options,
    snapshot,
    hasStaleOption,
    isLoading,
    error,
    refresh: fetchOptions,
    generate,
    recalculate,
    execute,
  };
}
