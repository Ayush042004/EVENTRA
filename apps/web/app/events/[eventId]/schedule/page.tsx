"use client";

import React, { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import {
  Calendar,
  Clock,
  AlertTriangle,
  CheckCircle,
  Play,
  Flame,
  ArrowRight,
  Filter,
  RefreshCw,
  Zap,
} from "lucide-react";
import { getSchedule, computeSchedule } from "../../../../lib/api/schedule";
import type { ScheduleResponse, TaskScheduleResponse } from "../../../../types/api";

export default function SchedulePage() {
  const params = useParams();
  const eventId = params.eventId as string;

  const [schedule, setSchedule] = useState<ScheduleResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [computing, setComputing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filterCritical, setFilterCritical] = useState(false);

  async function loadSchedule() {
    try {
      setLoading(true);
      setError(null);
      const data = await getSchedule(eventId);
      setSchedule(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load schedule";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  async function handleCompute() {
    try {
      setComputing(true);
      setError(null);
      const data = await computeSchedule(eventId);
      setSchedule(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to compute schedule";
      setError(msg);
    } finally {
      setComputing(false);
    }
  }

  useEffect(() => {
    if (eventId) {
      loadSchedule();
    }
  }, [eventId]);

  const entries = schedule?.entries || [];
  const filteredEntries = filterCritical
    ? entries.filter((e) => e.is_critical_path)
    : entries;

  // Compute relative positions for visual Gantt representation
  const minTime = schedule?.event_start ? new Date(schedule.event_start).getTime() : 0;
  const maxTime = schedule?.project_end
    ? new Date(schedule.project_end).getTime()
    : schedule?.event_end
    ? new Date(schedule.event_end).getTime()
    : minTime + 3600000;
  const timeSpan = Math.max(maxTime - minTime, 1);

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border/40 pb-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              Schedule & Critical Path Engine
            </h1>
            {schedule && (
              <span
                className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                  schedule.is_feasible
                    ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                    : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                }`}
              >
                {schedule.is_feasible ? (
                  <CheckCircle className="w-3.5 h-3.5" />
                ) : (
                  <AlertTriangle className="w-3.5 h-3.5" />
                )}
                {schedule.is_feasible ? "FEASIBLE" : "INFEASIBLE"}
              </span>
            )}
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            Deterministic CPM (Critical Path Method) schedule forward-pass calculations and slack telemetry.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={loadSchedule}
            disabled={loading}
            className="inline-flex items-center gap-2 px-3 py-1.5 text-xs font-medium rounded-lg border border-border/60 hover:bg-card/60 text-muted-foreground hover:text-foreground transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
          <button
            onClick={handleCompute}
            disabled={computing}
            className="inline-flex items-center gap-2 px-4 py-1.5 text-xs font-semibold rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground shadow-sm transition-colors"
          >
            <Play className={`w-3.5 h-3.5 ${computing ? "animate-spin" : ""}`} />
            {computing ? "Computing CPM..." : "Recompute Schedule"}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl border border-rose-500/30 bg-rose-500/5 text-rose-300 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{error}</span>
          </div>
          <button
            onClick={handleCompute}
            className="underline font-semibold hover:text-rose-200"
          >
            Run Forward Pass
          </button>
        </div>
      )}

      {/* KPI Telemetry Tiles */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm">
          <div className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-blue-400" />
            Total Duration
          </div>
          <div className="text-2xl font-bold tracking-tight text-foreground mt-2">
            {schedule?.total_duration_minutes ?? 0}{" "}
            <span className="text-xs font-normal text-muted-foreground">mins</span>
          </div>
          <div className="text-[11px] text-muted-foreground mt-1">
            {schedule?.total_duration_minutes
              ? `${(schedule.total_duration_minutes / 60).toFixed(1)} operational hours`
              : "Not scheduled yet"}
          </div>
        </div>

        <div className="p-4 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm">
          <div className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5 text-emerald-400" />
            Schedule Buffer
          </div>
          <div className="text-2xl font-bold tracking-tight text-emerald-400 mt-2">
            {schedule?.buffer_minutes ?? 0}{" "}
            <span className="text-xs font-normal text-muted-foreground">mins</span>
          </div>
          <div className="text-[11px] text-muted-foreground mt-1">
            Reserve slack before event hard end
          </div>
        </div>

        <div className="p-4 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm">
          <div className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
            <Flame className="w-3.5 h-3.5 text-amber-400" />
            Critical Path Tasks
          </div>
          <div className="text-2xl font-bold tracking-tight text-amber-400 mt-2">
            {schedule?.critical_path?.critical_path_tasks?.length ?? 0}
          </div>
          <div className="text-[11px] text-muted-foreground mt-1">
            Zero slack bottleneck tasks
          </div>
        </div>

        <div className="p-4 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm">
          <div className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-purple-400" />
            Projected End
          </div>
          <div className="text-sm font-semibold tracking-tight text-foreground mt-2 truncate">
            {schedule?.project_end
              ? new Date(schedule.project_end).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })
              : "N/A"}
          </div>
          <div className="text-[11px] text-muted-foreground mt-1 truncate">
            {schedule?.project_end
              ? new Date(schedule.project_end).toLocaleDateString()
              : "Awaiting calculation"}
          </div>
        </div>
      </div>

      {/* Critical Path Callout Banner */}
      {schedule?.critical_path && schedule.critical_path.critical_path_tasks.length > 0 && (
        <div className="p-4 rounded-xl border border-amber-500/30 bg-amber-500/5 backdrop-blur-sm">
          <div className="flex items-start justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Flame className="w-4 h-4 text-amber-400 shrink-0" />
                <span className="text-xs font-semibold uppercase tracking-wider text-amber-300">
                  Active Critical Path
                </span>
                <span className="text-[11px] text-muted-foreground">
                  ({schedule.critical_path.total_duration_minutes} min chain)
                </span>
              </div>
              <p className="text-xs text-muted-foreground">
                Delays on these tasks directly slip the overall event completion time:
              </p>
              <div className="flex flex-wrap items-center gap-2 pt-2">
                {schedule.critical_path.critical_path_tasks.map((taskId, idx) => {
                  const entry = entries.find((e) => e.task_id === taskId);
                  return (
                    <React.Fragment key={taskId}>
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-amber-500/10 border border-amber-500/30 text-amber-200 text-xs font-medium">
                        <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
                        {entry?.task_name || taskId.slice(0, 8)}
                      </span>
                      {idx < schedule.critical_path.critical_path_tasks.length - 1 && (
                        <ArrowRight className="w-3 h-3 text-muted-foreground shrink-0" />
                      )}
                    </React.Fragment>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filter and Schedule Matrix */}
      <div className="rounded-xl border border-border/50 bg-card/30 backdrop-blur-sm overflow-hidden">
        <div className="p-4 border-b border-border/40 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h2 className="text-sm font-semibold text-foreground">
              Forward-Pass Task Timeline & Slack Matrix
            </h2>
            <span className="text-xs text-muted-foreground">
              ({filteredEntries.length} tasks)
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setFilterCritical(!filterCritical)}
              className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium border transition-colors ${
                filterCritical
                  ? "bg-amber-500/20 text-amber-300 border-amber-500/40"
                  : "border-border/60 hover:bg-card text-muted-foreground hover:text-foreground"
              }`}
            >
              <Filter className="w-3 h-3" />
              Critical Only
            </button>
          </div>
        </div>

        {entries.length === 0 ? (
          <div className="p-12 text-center space-y-4">
            <Clock className="w-10 h-10 text-muted-foreground/40 mx-auto" />
            <div className="space-y-1">
              <h3 className="text-sm font-semibold text-foreground">
                No Schedule Computed
              </h3>
              <p className="text-xs text-muted-foreground max-w-sm mx-auto">
                Tasks have not been scheduled yet or a plan has not been generated. Compute forward-pass to establish planned start/end times and CPM slack.
              </p>
            </div>
            <button
              onClick={handleCompute}
              disabled={computing}
              className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground shadow-sm transition-colors"
            >
              <Play className="w-3.5 h-3.5" />
              {computing ? "Computing..." : "Compute Schedule Now"}
            </button>
          </div>
        ) : (
          <div className="divide-y divide-border/30">
            {filteredEntries.map((task) => {
              const startMs = task.planned_start
                ? new Date(task.planned_start).getTime()
                : minTime;
              const endMs = task.planned_end
                ? new Date(task.planned_end).getTime()
                : startMs + task.duration_minutes * 60000;

              const leftPercent = Math.max(
                0,
                Math.min(100, ((startMs - minTime) / timeSpan) * 100)
              );
              const widthPercent = Math.max(
                2,
                Math.min(100 - leftPercent, ((endMs - startMs) / timeSpan) * 100)
              );

              return (
                <div
                  key={task.task_id}
                  className="p-4 hover:bg-card/40 transition-colors space-y-2"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      {task.is_critical_path ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40">
                          <Flame className="w-2.5 h-2.5" />
                          CRITICAL
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium bg-secondary text-secondary-foreground border border-border/40">
                          SLACK {task.slack_minutes ?? 0}m
                        </span>
                      )}
                      <span className="text-xs font-semibold text-foreground">
                        {task.task_name}
                      </span>
                    </div>

                    <div className="flex items-center gap-4 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3 text-muted-foreground/70" />
                        {task.duration_minutes} min
                      </span>
                      <span>
                        {task.planned_start
                          ? new Date(task.planned_start).toLocaleTimeString([], {
                              hour: "2-digit",
                              minute: "2-digit",
                            })
                          : "TBD"}{" "}
                        &rarr;{" "}
                        {task.planned_end
                          ? new Date(task.planned_end).toLocaleTimeString([], {
                              hour: "2-digit",
                              minute: "2-digit",
                            })
                          : "TBD"}
                      </span>
                    </div>
                  </div>

                  {/* Gantt Bar Visualizer */}
                  <div className="w-full bg-secondary/30 h-3 rounded-full relative overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        task.is_critical_path
                          ? "bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.5)]"
                          : "bg-blue-500/80"
                      }`}
                      style={{
                        marginLeft: `${leftPercent}%`,
                        width: `${widthPercent}%`,
                      }}
                      title={`${task.task_name}: ${task.duration_minutes} min`}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
