"use client";

import React, { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import {
  FileText,
  Shield,
  RefreshCw,
  Clock,
  Layers,
  ChevronDown,
  ChevronRight,
  AlertTriangle,
  CheckCircle,
} from "lucide-react";
import { getAuditTrail } from "../../../../lib/api/observability";
import type { AuditRecordResponse } from "../../../../types/api";

export default function AuditPage() {
  const params = useParams();
  const eventId = params.eventId as string;

  const [records, setRecords] = useState<AuditRecordResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [filterAction, setFilterAction] = useState<string>("ALL");

  async function loadAudit() {
    try {
      setLoading(true);
      setError(null);
      const res = await getAuditTrail(eventId);
      setRecords(res.items || []);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load audit records";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (eventId) {
      loadAudit();
    }
  }, [eventId]);

  const filtered =
    filterAction === "ALL"
      ? records
      : records.filter((r) => r.action_type === filterAction);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border/40 pb-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
              <Shield className="w-6 h-6 text-primary" />
              Immutable Governance Audit Log
            </h1>
            <span className="font-mono text-[10px] px-2.5 py-0.5 rounded-full bg-secondary text-muted-foreground border border-border/50">
              Tamper-evident
            </span>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            Authoritative append-only ledger of state transitions, before/after mutations, and actor authorization proofs.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={loadAudit}
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

      {/* Audit Records Table */}
      <div className="rounded-xl border border-border/50 bg-card/30 backdrop-blur-sm overflow-hidden">
        <div className="p-4 border-b border-border/40 flex items-center justify-between text-xs text-muted-foreground">
          <span className="font-semibold uppercase text-[10px] tracking-wider text-foreground">
            Audit Ledger ({filtered.length} entries)
          </span>
          <span className="font-mono text-[10px]">SHA-256 State Anchored</span>
        </div>

        {filtered.length === 0 ? (
          <div className="p-12 text-center text-xs text-muted-foreground space-y-2">
            <FileText className="w-8 h-8 text-muted-foreground/40 mx-auto" />
            <p>No audit trail records committed yet.</p>
          </div>
        ) : (
          <div className="divide-y divide-border/30">
            {filtered.map((record) => {
              const isExpanded = expandedId === record.id;
              const hasDiff =
                record.before_state || record.after_state;

              return (
                <div
                  key={record.id}
                  className="p-4 hover:bg-card/40 transition-colors space-y-2"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-secondary text-secondary-foreground border border-border/50">
                          {record.action_type}
                        </span>
                        <span className="text-xs font-bold text-foreground">
                          {record.action}
                        </span>
                        {record.impact_level && (
                          <span
                            className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${
                              record.impact_level === "CRITICAL"
                                ? "bg-rose-500/20 text-rose-300"
                                : "bg-blue-500/20 text-blue-300"
                            }`}
                          >
                            {record.impact_level}
                          </span>
                        )}
                      </div>

                      <div className="text-[11px] text-muted-foreground flex flex-wrap items-center gap-3">
                        <span>
                          Actor: <strong>{record.actor_id || "SYSTEM"}</strong> ({record.actor_type})
                        </span>
                        {record.target_type && (
                          <span>
                            Target: {record.target_type} ({record.target_id || "fleet"})
                          </span>
                        )}
                        {record.approval_id && (
                          <span className="text-amber-400 font-mono">
                            Approval #{record.approval_id.slice(0, 8)}
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-3 shrink-0">
                      <span className="text-[11px] font-mono text-muted-foreground">
                        {new Date(record.created_at).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                          second: "2-digit",
                        })}
                      </span>

                      {hasDiff && (
                        <button
                          onClick={() => setExpandedId(isExpanded ? null : record.id)}
                          className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs text-muted-foreground hover:text-foreground border border-border/40 hover:bg-card"
                        >
                          <span>State Diff</span>
                          {isExpanded ? (
                            <ChevronDown className="w-3.5 h-3.5" />
                          ) : (
                            <ChevronRight className="w-3.5 h-3.5" />
                          )}
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Before / After State Inspector */}
                  {isExpanded && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
                      <div className="space-y-1">
                        <span className="text-[10px] font-semibold text-rose-300 uppercase tracking-wider">
                          Before State Snapshot
                        </span>
                        <div className="p-3 rounded-lg bg-background/60 border border-border/40 font-mono text-[10px] text-muted-foreground max-h-48 overflow-y-auto whitespace-pre-wrap">
                          {JSON.stringify(record.before_state || {}, null, 2)}
                        </div>
                      </div>

                      <div className="space-y-1">
                        <span className="text-[10px] font-semibold text-emerald-300 uppercase tracking-wider">
                          After State Snapshot
                        </span>
                        <div className="p-3 rounded-lg bg-background/60 border border-border/40 font-mono text-[10px] text-foreground max-h-48 overflow-y-auto whitespace-pre-wrap">
                          {JSON.stringify(record.after_state || {}, null, 2)}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
