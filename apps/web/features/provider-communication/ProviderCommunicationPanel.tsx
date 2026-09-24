"use client";

import React, { useState, useEffect } from "react";
import {
  MessageSquare,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Sparkles,
  Send,
  RefreshCw,
  ShieldCheck,
  UserCheck,
  Phone,
  DollarSign,
  Radio,
  ExternalLink,
} from "lucide-react";
import {
  getNegotiationConversation,
  negotiateWithProvider,
  requestEngagementApproval,
  confirmProviderEngagement,
  simulateProviderResponse,
  getOpenWAStatus,
  NegotiationConversation,
  OpenWAStatus,
  ProviderMessageItem,
} from "@/lib/api/negotiation";
import { approveRequest } from "@/lib/api/approvals";

interface ProviderCommunicationPanelProps {
  assignmentId: string;
  eventId: string;
  onRefresh?: () => void;
  compact?: boolean;
}

export function ProviderCommunicationPanel({
  assignmentId,
  eventId,
  onRefresh,
  compact = false,
}: ProviderCommunicationPanelProps) {
  const [conversation, setConversation] = useState<NegotiationConversation | null>(null);
  const [openwaStatus, setOpenwaStatus] = useState<OpenWAStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Simulation controls
  const [showSimControls, setShowSimControls] = useState(false);
  const [simScenario, setSimScenario] = useState<"ACCEPT" | "COUNTER" | "DECLINE">("ACCEPT");
  const [simQuote, setSimQuote] = useState<number>(42000);
  const [simCustomText, setSimCustomText] = useState("");

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [conv, owa] = await Promise.all([
        getNegotiationConversation(assignmentId),
        getOpenWAStatus().catch(() => null),
      ]);
      setConversation(conv);
      if (owa) setOpenwaStatus(owa);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load conversation");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (assignmentId) {
      loadData();
    }
  }, [assignmentId]);

  const assignment = conversation?.assignment as any;
  const vendor = conversation?.vendor as any;
  const messages = ((conversation?.messages || []) as unknown) as ProviderMessageItem[];

  const handleNegotiate = async () => {
    try {
      setActionLoading(true);
      setError(null);
      await negotiateWithProvider(assignmentId);
      setActionSuccess("Counter-offer sent to provider.");
      await loadData();
      onRefresh?.();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Negotiation counter-offer failed");
    } finally {
      setActionLoading(false);
    }
  };

  const handleRequestApproval = async () => {
    try {
      setActionLoading(true);
      setError(null);
      await requestEngagementApproval(assignmentId);
      setActionSuccess("Governance approval request created.");
      await loadData();
      onRefresh?.();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to request approval");
    } finally {
      setActionLoading(false);
    }
  };

  const handleApproveAndConfirm = async () => {
    try {
      setActionLoading(true);
      setError(null);
      if (assignment?.approval_id) {
        await approveRequest(
          eventId,
          assignment.approval_id,
          "Approved via operations agent drawer"
        );
      }
      await confirmProviderEngagement(assignmentId);
      setActionSuccess("Engagement approved & confirmed! Confirmation dispatched to WhatsApp.");
      await loadData();
      onRefresh?.();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Confirmation failed");
    } finally {
      setActionLoading(false);
    }
  };

  const handleSimulate = async () => {
    try {
      setActionLoading(true);
      setError(null);
      await simulateProviderResponse(assignmentId, {
        scenario: simScenario,
        quoted_amount: simScenario === "ACCEPT" || simScenario === "COUNTER" ? simQuote : undefined,
        message: simCustomText.trim() || undefined,
      });
      setActionSuccess(`Simulated provider response (${simScenario}) processed.`);
      setSimCustomText("");
      await loadData();
      onRefresh?.();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Simulation failed");
    } finally {
      setActionLoading(false);
    }
  };

  if (loading && !conversation) {
    return (
      <div className="p-6 rounded-xl border border-border/50 bg-secondary/10 flex items-center justify-center gap-2 text-xs text-muted-foreground">
        <RefreshCw className="w-4 h-4 animate-spin text-primary" />
        Loading communication thread...
      </div>
    );
  }

  const isSimulatedAssignment = assignment?.is_simulation;
  const isWhatsappActive = openwaStatus?.enabled && openwaStatus?.session?.connected;
  const status = assignment?.negotiation_status || "DISCOVERED";

  return (
    <div className="rounded-xl border border-border/60 bg-card/80 overflow-hidden shadow-lg space-y-0 text-xs">
      {/* Panel Header */}
      <div className="p-3.5 bg-secondary/30 border-b border-border/50 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <MessageSquare className="w-3.5 h-3.5" />
          </div>
          <div>
            <div className="font-semibold text-foreground flex items-center gap-2">
              <span>{vendor?.name || "Provider"}</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-secondary text-muted-foreground font-mono">
                {assignment?.category || "Service"}
              </span>
            </div>
            <div className="text-[11px] text-muted-foreground flex items-center gap-1.5">
              <span>Status: <strong className="text-foreground">{status}</strong></span>
              {vendor?.contact_phone && (
                <span>&bull; {vendor.contact_phone}</span>
              )}
            </div>
          </div>
        </div>

        {/* Channel Indicator Badge */}
        <div className="flex items-center gap-1.5">
          {isSimulatedAssignment ? (
            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
              DEMO SIMULATION
            </span>
          ) : isWhatsappActive ? (
            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              WHATSAPP (OpenWA)
            </span>
          ) : (
            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-500/10 text-slate-400 border border-slate-500/20">
              MOCK / SIMULATION
            </span>
          )}
          <button
            onClick={loadData}
            disabled={loading}
            className="p-1 rounded hover:bg-secondary text-muted-foreground"
            title="Refresh conversation"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Negotiation Financial & Timing Snapshot */}
      <div className="grid grid-cols-3 gap-2 p-3 bg-secondary/10 border-b border-border/40 text-center">
        <div className="p-2 rounded-lg bg-background/50 border border-border/30">
          <div className="text-[10px] text-muted-foreground">Quoted Rate</div>
          <div className="font-bold text-foreground text-xs mt-0.5">
            {assignment?.quoted_amount
              ? `${assignment.currency || "INR"} ${assignment.quoted_amount.toLocaleString()}`
              : "Pending Quote"}
          </div>
        </div>
        <div className="p-2 rounded-lg bg-background/50 border border-border/30">
          <div className="text-[10px] text-muted-foreground">Target Budget</div>
          <div className="font-bold text-emerald-400 text-xs mt-0.5">
            {assignment?.target_amount
              ? `${assignment.currency || "INR"} ${assignment.target_amount.toLocaleString()}`
              : "N/A"}
          </div>
        </div>
        <div className="p-2 rounded-lg bg-background/50 border border-border/30">
          <div className="text-[10px] text-muted-foreground">Approved Ceiling</div>
          <div className="font-bold text-amber-400 text-xs mt-0.5">
            {assignment?.max_approved_amount
              ? `${assignment.currency || "INR"} ${assignment.max_approved_amount.toLocaleString()}`
              : "N/A"}
          </div>
        </div>
      </div>

      {/* Alerts */}
      {error && (
        <div className="m-3 p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
          <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
          <span>{error}</span>
        </div>
      )}
      {actionSuccess && (
        <div className="m-3 p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
          <span>{actionSuccess}</span>
        </div>
      )}

      {/* Message Thread */}
      <div className="p-3.5 space-y-2.5 max-h-72 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="p-6 text-center text-muted-foreground text-xs">
            No messages exchanged yet with this provider.
          </div>
        ) : (
          messages.map((m, idx) => {
            const isOutbound = m.direction === "OUTBOUND";
            const isSim = m.channel === "DEMO_SIMULATION" || m.is_simulation;
            return (
              <div
                key={m.id || idx}
                className={`flex flex-col ${isOutbound ? "items-end" : "items-start"}`}
              >
                <div
                  className={`max-w-[85%] rounded-xl p-3 text-xs leading-relaxed ${
                    isOutbound
                      ? "bg-primary text-primary-foreground rounded-br-none"
                      : "bg-secondary/70 border border-border/50 text-foreground rounded-bl-none"
                  }`}
                >
                  <p className="whitespace-pre-wrap">{m.message}</p>
                </div>
                <div className="flex items-center gap-1.5 mt-1 text-[10px] text-muted-foreground px-1">
                  <span>{isOutbound ? "EVENTRA" : vendor?.name || "Provider"}</span>
                  {isSim ? (
                    <span className="px-1 rounded bg-amber-500/10 text-amber-400 font-mono text-[9px] border border-amber-500/20">
                      DEMO SIMULATION
                    </span>
                  ) : (
                    <span className="px-1 rounded bg-emerald-500/10 text-emerald-400 font-mono text-[9px]">
                      WHATSAPP
                    </span>
                  )}
                  {m.timestamp && (
                    <span>
                      &bull; {new Date(typeof m.timestamp === "number" && m.timestamp < 10000000000 ? m.timestamp * 1000 : m.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </span>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Action Bar */}
      <div className="p-3 bg-secondary/20 border-t border-border/50 space-y-2">
        <div className="flex flex-wrap items-center gap-2">
          {/* Status-specific actions */}
          {status === "QUOTATION_RECEIVED" && (
            <button
              onClick={handleNegotiate}
              disabled={actionLoading}
              className="px-3 py-1.5 rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground font-semibold flex items-center gap-1.5 transition disabled:opacity-50"
            >
              <Sparkles className="w-3.5 h-3.5" />
              Counter-Offer toward Target
            </button>
          )}

          {status === "AWAITING_APPROVAL" && (
            <>
              {!assignment?.approval_id ? (
                <button
                  onClick={handleRequestApproval}
                  disabled={actionLoading}
                  className="px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-600 text-white font-semibold flex items-center gap-1.5 transition disabled:opacity-50"
                >
                  <ShieldCheck className="w-3.5 h-3.5" />
                  Request Governance Approval
                </button>
              ) : (
                <button
                  onClick={handleApproveAndConfirm}
                  disabled={actionLoading}
                  className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-semibold flex items-center gap-1.5 transition disabled:opacity-50 shadow-md"
                >
                  <UserCheck className="w-3.5 h-3.5" />
                  Approve & Confirm Provider
                </button>
              )}
            </>
          )}

          {status === "CONFIRMED" && (
            <div className="px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-semibold flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Confirmed at {assignment.currency || "INR"} {assignment.agreed_cost?.toLocaleString()}
            </div>
          )}

          {/* Toggle Simulation Drawer */}
          <button
            onClick={() => setShowSimControls(!showSimControls)}
            className="ml-auto text-[11px] text-muted-foreground hover:text-foreground px-2 py-1 rounded bg-secondary/50 border border-border/30"
          >
            {showSimControls ? "Hide Demo Simulator" : "Demo Simulator"}
          </button>
        </div>

        {/* Demo Simulator Controls */}
        {showSimControls && (
          <div className="p-3 rounded-lg border border-amber-500/30 bg-amber-500/5 space-y-2 mt-2">
            <div className="flex items-center justify-between text-[11px] font-bold text-amber-300">
              <span>Demo WhatsApp Provider Response Simulator</span>
              <span className="text-[10px] text-amber-400/80 font-normal">All events tagged DEMO SIMULATION</span>
            </div>
            <div className="grid grid-cols-3 gap-2">
              <button
                onClick={() => setSimScenario("ACCEPT")}
                className={`py-1 px-2 rounded text-[11px] border font-medium ${
                  simScenario === "ACCEPT"
                    ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                    : "bg-secondary text-muted-foreground border-border/30"
                }`}
              >
                Accept Offer
              </button>
              <button
                onClick={() => setSimScenario("COUNTER")}
                className={`py-1 px-2 rounded text-[11px] border font-medium ${
                  simScenario === "COUNTER"
                    ? "bg-amber-500/20 text-amber-300 border-amber-500/40"
                    : "bg-secondary text-muted-foreground border-border/30"
                }`}
              >
                Counter-Offer
              </button>
              <button
                onClick={() => setSimScenario("DECLINE")}
                className={`py-1 px-2 rounded text-[11px] border font-medium ${
                  simScenario === "DECLINE"
                    ? "bg-rose-500/20 text-rose-300 border-rose-500/40"
                    : "bg-secondary text-muted-foreground border-border/30"
                }`}
              >
                Decline
              </button>
            </div>

            {simScenario !== "DECLINE" && (
              <div className="flex items-center gap-2">
                <span className="text-[11px] text-muted-foreground">Simulated Quoted Price:</span>
                <input
                  type="number"
                  value={simQuote}
                  onChange={(e) => setSimQuote(Number(e.target.value))}
                  className="w-28 px-2 py-1 bg-background border border-border/50 rounded text-foreground text-xs"
                />
              </div>
            )}

            <button
              onClick={handleSimulate}
              disabled={actionLoading}
              className="w-full py-1.5 bg-amber-500 hover:bg-amber-600 text-white font-semibold rounded text-xs transition disabled:opacity-50"
            >
              {actionLoading ? "Dispatching..." : `Trigger Simulated ${simScenario} Message`}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
