"use client";

import React, { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import {
  BarChart3,
  TrendingUp,
  Clock,
  DollarSign,
  ShieldAlert,
  Zap,
  CheckCircle,
  RefreshCw,
  Layers,
} from "lucide-react";
import { getEvent } from "../../../../lib/api/events";
import { getSchedule } from "../../../../lib/api/schedule";
import { getBudgetSummary } from "../../../../lib/api/budget";
import { listIncidents } from "../../../../lib/api/incidents";
import type {
  EventResponse,
  ScheduleResponse,
  BudgetSummaryResponse,
  IncidentResponse,
} from "../../../../types/api";

export default function AnalyticsPage() {
  const params = useParams();
  const eventId = params.eventId as string;

  const [event, setEvent] = useState<EventResponse | null>(null);
  const [schedule, setSchedule] = useState<ScheduleResponse | null>(null);
  const [budget, setBudget] = useState<BudgetSummaryResponse | null>(null);
  const [incidents, setIncidents] = useState<IncidentResponse[]>([]);
  const [loading, setLoading] = useState(true);

  async function loadData() {
    try {
      setLoading(true);
      const [ev, sc, bg, inc] = await Promise.all([
        getEvent(eventId).catch(() => null),
        getSchedule(eventId).catch(() => null),
        getBudgetSummary(eventId).catch(() => null),
        listIncidents(eventId).catch(() => ({ items: [] })),
      ]);
      setEvent(ev);
      setSchedule(sc);
      setBudget(bg);
      setIncidents(inc?.items || []);
    } catch (err: unknown) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (eventId) {
      loadData();
    }
  }, [eventId]);

  const totalBudget = budget?.total_budget || Number(event?.total_budget) || 0;
  const totalActual = budget?.total_actual || 0;
  const budgetUtilization = totalBudget > 0 ? (totalActual / totalBudget) * 100 : 0;

  const criticalTasksCount = schedule?.critical_path?.critical_path_tasks?.length || 0;
  const totalTasks = schedule?.entries?.length || 0;
  const criticalRatio = totalTasks > 0 ? (criticalTasksCount / totalTasks) * 100 : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border/40 pb-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
              <BarChart3 className="w-6 h-6 text-primary" />
              Event Operations Analytics & Reliability Telemetry
            </h1>
            <span className="font-mono text-[10px] px-2.5 py-0.5 rounded-full bg-secondary text-muted-foreground border border-border/50">
              Aggregated Ops Metrics
            </span>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            CPM schedule adherence, financial utilization, incident recurrence rates, and operational resilience indexes.
          </p>
        </div>

        <button
          onClick={loadData}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-border/60 hover:bg-card/60 text-muted-foreground hover:text-foreground transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* Primary KPI Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm">
          <div className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-blue-400" />
            Schedule Resilience
          </div>
          <div className="text-2xl font-bold tracking-tight text-foreground mt-2">
            {schedule?.buffer_minutes ?? 0}{" "}
            <span className="text-xs font-normal text-muted-foreground">min buffer</span>
          </div>
          <div className="text-[11px] text-muted-foreground mt-1">
            Status: {schedule?.is_feasible ? "Feasible" : "Infeasible"}
          </div>
        </div>

        <div className="p-4 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm">
          <div className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
            <DollarSign className="w-3.5 h-3.5 text-emerald-400" />
            Budget Efficiency
          </div>
          <div className="text-2xl font-bold tracking-tight text-emerald-400 mt-2">
            {budgetUtilization.toFixed(1)}%
          </div>
          <div className="text-[11px] text-muted-foreground mt-1">
            ${budget?.remaining?.toLocaleString() || "0"} reserve
          </div>
        </div>

        <div className="p-4 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm">
          <div className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5 text-amber-400" />
            Critical Path Ratio
          </div>
          <div className="text-2xl font-bold tracking-tight text-amber-400 mt-2">
            {criticalRatio.toFixed(0)}%
          </div>
          <div className="text-[11px] text-muted-foreground mt-1">
            {criticalTasksCount} of {totalTasks} tasks on zero-slack path
          </div>
        </div>

        <div className="p-4 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm">
          <div className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
            <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
            Total Incidents
          </div>
          <div className="text-2xl font-bold tracking-tight text-foreground mt-2">
            {incidents.length}
          </div>
          <div className="text-[11px] text-muted-foreground mt-1">
            {incidents.filter((i) => i.status === "RESOLVED").length} resolved
          </div>
        </div>
      </div>

      {/* Analytics Visual Breakdown Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Schedule Breakdown */}
        <div className="p-5 rounded-xl border border-border/50 bg-card/30 backdrop-blur-sm space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <Clock className="w-4 h-4 text-blue-400" />
              Schedule Duration & Buffer Distribution
            </h3>
            <span className="text-xs text-muted-foreground">
              {schedule?.total_duration_minutes ?? 0} Total Mins
            </span>
          </div>

          <div className="space-y-3 text-xs">
            <div className="space-y-1">
              <div className="flex justify-between text-muted-foreground">
                <span>Critical Path Duration</span>
                <span className="font-mono text-amber-400 font-semibold">
                  {schedule?.critical_path?.total_duration_minutes ?? 0}m
                </span>
              </div>
              <div className="w-full bg-secondary/50 h-2 rounded-full overflow-hidden">
                <div
                  className="bg-amber-500 h-full rounded-full"
                  style={{
                    width: `${Math.min(
                      ((schedule?.critical_path?.total_duration_minutes || 0) /
                        Math.max(schedule?.total_duration_minutes || 1, 1)) *
                        100,
                      100
                    )}%`,
                  }}
                />
              </div>
            </div>

            <div className="space-y-1">
              <div className="flex justify-between text-muted-foreground">
                <span>Reserve Buffer Minutes</span>
                <span className="font-mono text-emerald-400 font-semibold">
                  {schedule?.buffer_minutes ?? 0}m
                </span>
              </div>
              <div className="w-full bg-secondary/50 h-2 rounded-full overflow-hidden">
                <div
                  className="bg-emerald-500 h-full rounded-full"
                  style={{
                    width: `${Math.min(
                      ((schedule?.buffer_minutes || 0) /
                        Math.max(schedule?.total_duration_minutes || 1, 1)) *
                        100,
                      100
                    )}%`,
                  }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Budget Category Allocation */}
        <div className="p-5 rounded-xl border border-border/50 bg-card/30 backdrop-blur-sm space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <DollarSign className="w-4 h-4 text-emerald-400" />
              Financial Allocation by Category
            </h3>
            <span className="text-xs text-muted-foreground">
              ${totalBudget.toLocaleString()}
            </span>
          </div>

          {budget?.categories && Object.keys(budget.categories).length > 0 ? (
            <div className="space-y-2">
              {Object.entries(budget.categories).map(([cat, amount]) => {
                const pct = totalBudget > 0 ? (amount / totalBudget) * 100 : 0;
                return (
                  <div key={cat} className="space-y-1 text-xs">
                    <div className="flex justify-between text-muted-foreground">
                      <span className="uppercase text-[11px]">{cat}</span>
                      <span className="font-mono text-foreground">
                        ${amount.toLocaleString()} ({pct.toFixed(0)}%)
                      </span>
                    </div>
                    <div className="w-full bg-secondary/50 h-1.5 rounded-full overflow-hidden">
                      <div
                        className="bg-primary h-full rounded-full"
                        style={{ width: `${Math.min(pct, 100)}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-xs text-muted-foreground italic py-4 text-center">
              No category allocations calculated yet.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
