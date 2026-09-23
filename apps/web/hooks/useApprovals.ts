"use client";

import { useState, useEffect, useCallback } from "react";
import {
  listApprovals,
  approveRequest as apiApprove,
  rejectRequest as apiReject,
  cancelRequest as apiCancel,
} from "../lib/api/approvals";
import type { ApprovalRequestResponse } from "../types/api";

export function useApprovals(eventId: string | null) {
  const [approvals, setApprovals] = useState<ApprovalRequestResponse[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchApprovals = useCallback(async () => {
    if (!eventId) return;
    try {
      const res = await listApprovals(eventId);
      setApprovals(res.items || []);
      setError(null);
    } catch (err: any) {
      setError(err?.message || "Failed to load approvals");
    } finally {
      setIsLoading(false);
    }
  }, [eventId]);

  useEffect(() => {
    if (!eventId) return;
    setIsLoading(true);
    fetchApprovals();
  }, [eventId, fetchApprovals]);

  const approve = async (approvalId: string, notes?: string) => {
    if (!eventId) return;
    setIsLoading(true);
    try {
      const res = await apiApprove(eventId, approvalId, notes);
      await fetchApprovals();
      return res;
    } catch (err: any) {
      setError(err?.message || "Approval decision failed");
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const reject = async (approvalId: string, reason: string) => {
    if (!eventId) return;
    setIsLoading(true);
    try {
      const res = await apiReject(eventId, approvalId, reason);
      await fetchApprovals();
      return res;
    } catch (err: any) {
      setError(err?.message || "Rejection failed");
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const cancel = async (approvalId: string, reason?: string) => {
    if (!eventId) return;
    setIsLoading(true);
    try {
      const res = await apiCancel(eventId, approvalId, reason);
      await fetchApprovals();
      return res;
    } catch (err: any) {
      setError(err?.message || "Cancellation failed");
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const pendingCount = approvals.filter((a) => a.status === "PENDING").length;

  return {
    approvals,
    pendingCount,
    isLoading,
    error,
    refresh: fetchApprovals,
    approve,
    reject,
    cancel,
  };
}
