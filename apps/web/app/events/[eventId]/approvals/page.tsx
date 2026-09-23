"use client";

import React, { useState, useEffect } from "react";
import { useParams, useSearchParams } from "next/navigation";
import {
  ShieldCheck,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  RefreshCw,
  UserCheck,
  UserX,
  ArrowRight,
  Info,
  X,
  FileCheck,
} from "lucide-react";
import {
  listApprovals,
  approveRequest,
  rejectRequest,
  cancelRequest,
} from "../../../../lib/api/approvals";
import { useUiStore } from "../../../../stores/uiStore";
import type {
  ApprovalRequestResponse,
  ApprovalStatus,
} from "../../../../types/api";

export default function ApprovalsPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const eventId = params.eventId as string;
  const initialApprovalId = searchParams.get("approvalId");

  const { currentOperator } = useUiStore();

  const [approvals, setApprovals] = useState<ApprovalRequestResponse[]>([]);
  const [selectedApproval, setSelectedApproval] = useState<ApprovalRequestResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");

  // Reject modal
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [rejectionReason, setRejectionReason] = useState("");

  // Decision notes for approve
  const [decisionNotes, setDecisionNotes] = useState("");

  async function loadApprovals() {
    try {
      setLoading(true);
      setError(null);
      const res = await listApprovals(eventId);
      setApprovals(res.items);

      if (res.items.length > 0) {
        if (initialApprovalId) {
          const match = res.items.find((a: ApprovalRequestResponse) => a.id === initialApprovalId);
          setSelectedApproval(match || res.items[0]);
        } else if (!selectedApproval) {
          setSelectedApproval(res.items[0]);
        }
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load approval requests";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (eventId) {
      loadApprovals();
    }
  }, [eventId]);

  async function handleApprove() {
    if (!selectedApproval) return;
    try {
      setActionLoading(true);
      setError(null);
      const updated = await approveRequest(eventId, selectedApproval.id, decisionNotes);
      setSelectedApproval(updated);
      setDecisionNotes("");
      await loadApprovals();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to approve request";
      setError(msg);
    } finally {
      setActionLoading(false);
    }
  }

  async function handleReject() {
    if (!selectedApproval || !rejectionReason.trim()) return;
    try {
      setActionLoading(true);
      setError(null);
      const updated = await rejectRequest(eventId, selectedApproval.id, rejectionReason);
      setSelectedApproval(updated);
      setShowRejectModal(false);
      setRejectionReason("");
      await loadApprovals();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to reject request";
      setError(msg);
    } finally {
      setActionLoading(false);
    }
  }

  async function handleCancel() {
    if (!selectedApproval) return;
    try {
      setActionLoading(true);
      setError(null);
      const updated = await cancelRequest(eventId, selectedApproval.id, "Operator retracted request");
      setSelectedApproval(updated);
      await loadApprovals();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to cancel request";
      setError(msg);
    } finally {
      setActionLoading(false);
    }
  }

  const filteredApprovals =
    statusFilter === "ALL"
      ? approvals
      : approvals.filter((a) => a.status === statusFilter);

  // Separation of duties check:
  // Is current operator the requester?
  const isRequester =
    selectedApproval?.requester_id === currentOperator.id;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border/40 pb-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
              <ShieldCheck className="w-6 h-6 text-emerald-400" />
              Governance & Approvals Queue
            </h1>
            <span className="font-mono text-[10px] px-2.5 py-0.5 rounded-full bg-secondary text-muted-foreground border border-border/50">
              RBAC Separation of Duties
            </span>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            Authoritative gate for high-impact actions, budget deviations, and operational recovery plans.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={loadApprovals}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-border/60 hover:bg-card/60 text-muted-foreground hover:text-foreground transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl border border-rose-500/30 bg-rose-500/5 text-rose-300 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Grid: Approvals List + Detail Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Approvals Roster */}
        <div className="lg:col-span-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Pending & Decided ({filteredApprovals.length})
            </div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="text-xs bg-card border border-border/50 rounded-lg px-2 py-1 text-foreground"
            >
              <option value="ALL">All Statuses</option>
              <option value="PENDING">PENDING</option>
              <option value="APPROVED">APPROVED</option>
              <option value="REJECTED">REJECTED</option>
              <option value="CANCELLED">CANCELLED</option>
            </select>
          </div>

          {filteredApprovals.length === 0 ? (
            <div className="p-8 text-center rounded-xl border border-border/50 bg-card/30 text-xs text-muted-foreground">
              No approval requests matching filter.
            </div>
          ) : (
            <div className="space-y-2">
              {filteredApprovals.map((req) => {
                const isSelected = selectedApproval?.id === req.id;
                return (
                  <div
                    key={req.id}
                    onClick={() => setSelectedApproval(req)}
                    className={`p-3.5 rounded-xl border cursor-pointer transition-all space-y-2 ${
                      isSelected
                        ? "bg-card border-primary shadow-md ring-1 ring-primary/20"
                        : "bg-card/40 border-border/40 hover:bg-card/70"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="space-y-0.5">
                        <span className="text-[10px] font-mono text-muted-foreground uppercase">
                          {req.action_type}
                        </span>
                        <h3 className="text-xs font-bold text-foreground">
                          {req.target_type} ({req.impact_level})
                        </h3>
                      </div>
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          req.status === "PENDING"
                            ? "bg-amber-500/20 text-amber-300 border border-amber-500/40 animate-pulse"
                            : req.status === "APPROVED"
                            ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                            : req.status === "REJECTED"
                            ? "bg-rose-500/20 text-rose-300 border border-rose-500/40"
                            : "bg-secondary text-muted-foreground"
                        }`}
                      >
                        {req.status}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-[11px] text-muted-foreground pt-1 border-t border-border/20">
                      <span>By: {req.requester_id}</span>
                      <span>{new Date(req.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Selected Approval Detail Inspector */}
        <div className="lg:col-span-8 space-y-5">
          {selectedApproval ? (
            <>
              {/* Separation of Duties Warning Banner */}
              {isRequester && selectedApproval.status === "PENDING" && (
                <div className="p-4 rounded-xl border border-amber-500/40 bg-amber-500/10 text-amber-200 text-xs space-y-1.5">
                  <div className="flex items-center gap-2 font-bold">
                    <UserX className="w-4 h-4 text-amber-400" />
                    Separation of Duties Constraint Enforced
                  </div>
                  <p className="text-[11px] opacity-90">
                    You are currently active as <strong>{currentOperator.name}</strong> ({currentOperator.id}), who authored this request. Under EVENTRA governance policy, the author cannot self-approve.
                  </p>
                  <p className="text-[11px] font-medium text-amber-300">
                    &rarr; Use the Persona Switcher in the top bar to switch to <strong>Operations Director</strong> to authorize this decision.
                  </p>
                </div>
              )}

              {/* Approval Info Card */}
              <div className="p-5 rounded-xl border border-border/60 bg-card/40 backdrop-blur-sm space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-[10px] uppercase px-2 py-0.5 rounded bg-secondary text-secondary-foreground border border-border/50">
                        {selectedApproval.action_type}
                      </span>
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                          selectedApproval.impact_level === "CRITICAL"
                            ? "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                            : "bg-blue-500/20 text-blue-300 border border-blue-500/30"
                        }`}
                      >
                        {selectedApproval.impact_level} IMPACT
                      </span>
                    </div>
                    <h2 className="text-base font-bold text-foreground">
                      Target: {selectedApproval.target_type}{" "}
                      {selectedApproval.target_id && `(${selectedApproval.target_id})`}
                    </h2>
                    <div className="text-xs text-muted-foreground flex items-center gap-4">
                      <span>Requester: <strong>{selectedApproval.requester_id}</strong></span>
                      <span>Snapshot: <code className="font-mono">{selectedApproval.state_snapshot?.slice(0, 8)}</code></span>
                      <span>Created: {new Date(selectedApproval.created_at).toLocaleString()}</span>
                    </div>
                  </div>

                  <span
                    className={`px-3 py-1 rounded-full text-xs font-extrabold uppercase tracking-wider self-start ${
                      selectedApproval.status === "PENDING"
                        ? "bg-amber-500/20 text-amber-300 border border-amber-500/40 animate-pulse"
                        : selectedApproval.status === "APPROVED"
                        ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                        : selectedApproval.status === "REJECTED"
                        ? "bg-rose-500/20 text-rose-300 border border-rose-500/40"
                        : "bg-secondary text-muted-foreground"
                    }`}
                  >
                    {selectedApproval.status}
                  </span>
                </div>

                {/* Requested Action JSON Payload */}
                <div className="space-y-1.5 text-xs">
                  <span className="font-semibold text-muted-foreground uppercase text-[10px] tracking-wider">
                    Requested Action Payload & Execution Arguments:
                  </span>
                  <div className="p-3.5 rounded-xl bg-background/60 border border-border/40 font-mono text-[11px] text-foreground/90 whitespace-pre-wrap max-h-64 overflow-y-auto">
                    {JSON.stringify(selectedApproval.requested_action, null, 2)}
                  </div>
                </div>

                {/* Decided Audit Trail if not pending */}
                {selectedApproval.status !== "PENDING" && (
                  <div className="p-3.5 rounded-xl bg-secondary/30 border border-border/40 text-xs space-y-1">
                    <div className="font-semibold text-foreground">
                      Decision Recorded by: {selectedApproval.approver_id || "System"}
                    </div>
                    {selectedApproval.decision_notes && (
                      <div className="text-muted-foreground">
                        Notes: {selectedApproval.decision_notes}
                      </div>
                    )}
                    {selectedApproval.rejection_reason && (
                      <div className="text-rose-400 font-semibold">
                        Rejection Reason: {selectedApproval.rejection_reason}
                      </div>
                    )}
                    <div className="text-[10px] text-muted-foreground">
                      Decided At: {selectedApproval.decided_at ? new Date(selectedApproval.decided_at).toLocaleString() : "N/A"}
                    </div>
                  </div>
                )}

                {/* Decision Action Bar (if PENDING) */}
                {selectedApproval.status === "PENDING" && (
                  <div className="pt-4 border-t border-border/30 space-y-3">
                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                        Approval Notes / Authorization Rationale (Optional)
                      </label>
                      <input
                        type="text"
                        placeholder="e.g. Authorized under contingency recovery protocol..."
                        value={decisionNotes}
                        onChange={(e) => setDecisionNotes(e.target.value)}
                        className="w-full p-2.5 rounded-lg bg-secondary/50 border border-border text-foreground text-xs"
                      />
                    </div>

                    <div className="flex items-center justify-between gap-3 pt-2">
                      <button
                        onClick={handleCancel}
                        disabled={actionLoading}
                        className="px-3 py-1.5 text-xs font-medium rounded-lg border border-border/60 hover:bg-card text-muted-foreground hover:text-foreground"
                      >
                        Cancel Request
                      </button>

                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => setShowRejectModal(true)}
                          disabled={actionLoading}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-rose-500/10 text-rose-300 border border-rose-500/30 hover:bg-rose-500/20"
                        >
                          <XCircle className="w-3.5 h-3.5" />
                          Reject
                        </button>

                        <button
                          onClick={handleApprove}
                          disabled={actionLoading || isRequester}
                          className={`inline-flex items-center gap-1.5 px-4 py-1.5 text-xs font-bold rounded-lg shadow-sm transition-colors ${
                            isRequester
                              ? "bg-secondary text-muted-foreground cursor-not-allowed"
                              : "bg-emerald-600 hover:bg-emerald-500 text-white"
                          }`}
                        >
                          <CheckCircle className="w-3.5 h-3.5" />
                          {actionLoading ? "Authorizing..." : "Approve & Execute Action"}
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="p-12 text-center rounded-xl border border-border/50 bg-card/30 text-xs text-muted-foreground">
              Select an approval request to inspect payload details and execute governance actions.
            </div>
          )}
        </div>
      </div>

      {/* Reject Modal */}
      {showRejectModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm">
          <div className="bg-card border border-border/60 rounded-2xl p-6 w-full max-w-md shadow-2xl space-y-4">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-base font-bold text-foreground">
                  Reject Approval Request
                </h3>
                <p className="text-xs text-muted-foreground mt-0.5">
                  State change will be blocked and recorded in the audit trail.
                </p>
              </div>
              <button
                onClick={() => setShowRejectModal(false)}
                className="text-muted-foreground hover:text-foreground p-1 rounded-lg"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div>
              <label className="block text-xs font-semibold text-muted-foreground mb-1">
                Reason for Rejection *
              </label>
              <textarea
                rows={3}
                required
                placeholder="Explain why this action was rejected..."
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                className="w-full p-2.5 rounded-lg bg-secondary/50 border border-border text-foreground text-xs"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-border/40">
              <button
                onClick={() => setShowRejectModal(false)}
                className="px-3 py-1.5 text-xs font-medium rounded-lg border border-border/60 hover:bg-card text-muted-foreground"
              >
                Cancel
              </button>
              <button
                onClick={handleReject}
                disabled={actionLoading || !rejectionReason.trim()}
                className="px-4 py-1.5 text-xs font-bold rounded-lg bg-rose-600 hover:bg-rose-500 text-white shadow-sm"
              >
                {actionLoading ? "Rejecting..." : "Confirm Rejection"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
