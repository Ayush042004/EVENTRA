"use client";

import React, { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import {
  History,
  Clock,
  RefreshCw,
  Filter,
  CheckCircle,
  AlertTriangle,
  Send,
  Shield,
  Layers,
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import { getActivityFeed } from "../../../../lib/api/observability";
import type { ActivityEntryResponse } from "../../../../types/api";

export default function ActivityPage() {
  const params = useParams();
  const eventId = params.eventId as string;

  const [activities, setActivities] = useState<ActivityEntryResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [categoryFilter, setCategoryFilter] = useState<string>("ALL");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  async function loadFeed() {
    try {
      setLoading(true);
      setError(null);
      const res = await getActivityFeed(eventId, 100);
      setActivities(res.items || []);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load activity stream";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (eventId) {
      loadFeed();
    }
  }, [eventId]);

  const filtered =
    categoryFilter === "ALL"
      ? activities
      : activities.filter(
          (a) => a.category?.toUpperCase() === categoryFilter.toUpperCase()
        );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border/40 pb-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
              <History className="w-6 h-6 text-primary" />
              Chronological Activity Stream
            </h1>
            <span className="font-mono text-[10px] px-2.5 py-0.5 rounded-full bg-secondary text-muted-foreground border border-border/50">
              Real-time Fleet Log
            </span>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            Unified human and autonomous agent action events across setup, live operations, and incident recoveries.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="text-xs bg-card border border-border/60 rounded-lg px-2.5 py-1.5 text-foreground"
          >
            <option value="ALL">All Categories</option>
            <option value="INCIDENT">INCIDENT</option>
            <option value="RECOVERY">RECOVERY</option>
            <option value="APPROVAL">APPROVAL</option>
            <option value="TASK">TASK</option>
            <option value="COMMUNICATION">COMMUNICATION</option>
            <option value="SYSTEM">SYSTEM</option>
          </select>

          <button
            onClick={loadFeed}
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

      {/* Activity Timeline List */}
      <div className="rounded-xl border border-border/50 bg-card/30 backdrop-blur-sm overflow-hidden">
        <div className="p-4 border-b border-border/40 flex items-center justify-between text-xs text-muted-foreground">
          <span className="font-semibold uppercase text-[10px] tracking-wider text-foreground">
            Activity Timeline ({filtered.length} entries)
          </span>
          <span>Ordered newest to oldest</span>
        </div>

        {filtered.length === 0 ? (
          <div className="p-12 text-center text-xs text-muted-foreground space-y-2">
            <History className="w-8 h-8 text-muted-foreground/40 mx-auto" />
            <p>No activity records logged for this event yet.</p>
          </div>
        ) : (
          <div className="divide-y divide-border/30">
            {filtered.map((item) => {
              const isExpanded = expandedId === item.id;
              const hasDetails =
                item.details && Object.keys(item.details).length > 0;

              return (
                <div
                  key={item.id}
                  className="p-4 hover:bg-card/40 transition-colors space-y-2"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-3">
                      <div className="mt-0.5">
                        <span
                          className={`w-2.5 h-2.5 rounded-full inline-block ${
                            item.category === "INCIDENT"
                              ? "bg-rose-400"
                              : item.category === "RECOVERY"
                              ? "bg-amber-400"
                              : item.category === "APPROVAL"
                              ? "bg-blue-400"
                              : "bg-emerald-400"
                          }`}
                        />
                      </div>
                      <div className="space-y-0.5">
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-secondary text-secondary-foreground border border-border/40">
                            {item.category}
                          </span>
                          <span className="text-xs font-semibold text-foreground">
                            {item.summary}
                          </span>
                        </div>
                        <div className="text-[11px] text-muted-foreground flex items-center gap-3">
                          {item.actor_id && (
                            <span>
                              Actor: <strong className="text-foreground">{item.actor_id}</strong>
                            </span>
                          )}
                          <span>Status: {item.status}</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 shrink-0">
                      <span className="text-[11px] font-mono text-muted-foreground">
                        {item.timestamp
                          ? new Date(item.timestamp).toLocaleTimeString([], {
                              hour: "2-digit",
                              minute: "2-digit",
                              second: "2-digit",
                            })
                          : "Just now"}
                      </span>

                      {hasDetails && (
                        <button
                          onClick={() => setExpandedId(isExpanded ? null : item.id)}
                          className="p-1 rounded text-muted-foreground hover:text-foreground"
                        >
                          {isExpanded ? (
                            <ChevronDown className="w-4 h-4" />
                          ) : (
                            <ChevronRight className="w-4 h-4" />
                          )}
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Expanded Payload Details */}
                  {isExpanded && hasDetails && (
                    <div className="pt-2">
                      <div className="p-3 rounded-xl bg-background/60 border border-border/40 font-mono text-[11px] text-foreground/90 whitespace-pre-wrap max-h-48 overflow-y-auto">
                        {JSON.stringify(item.details, null, 2)}
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
