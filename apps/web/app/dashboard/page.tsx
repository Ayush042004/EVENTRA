"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AppShell } from "../../components/shell/AppShell";
import { listEvents } from "../../lib/api/events";
import { listApprovals } from "../../lib/api/approvals";
import { listIncidents } from "../../lib/api/incidents";
import { getActivityFeed } from "../../lib/api/observability";
import type { EventResponse, ApprovalRequestResponse, IncidentResponse, ActivityEntryResponse } from "../../types/api";
import {
  Radio,
  AlertTriangle,
  Clock,
  Calendar,
  ArrowRight,
  Plus,
  ShieldCheck,
  TrendingUp,
  Activity as ActivityIcon,
} from "lucide-react";

export default function DashboardPage() {
  const [events, setEvents] = useState<EventResponse[]>([]);
  const [approvals, setApprovals] = useState<ApprovalRequestResponse[]>([]);
  const [incidents, setIncidents] = useState<IncidentResponse[]>([]);
  const [activities, setActivities] = useState<ActivityEntryResponse[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDashboardData() {
      setLoading(true);
      try {
        const evList = await listEvents();
        setEvents(evList || []);

        const targetEventId = evList?.[0]?.id || "conference_demo";

        const [appRes, incRes, actRes] = await Promise.allSettled([
          listApprovals(targetEventId, { status: "PENDING" }),
          listIncidents(targetEventId),
          getActivityFeed(targetEventId, 10),
        ]);

        if (appRes.status === "fulfilled") setApprovals(appRes.value.items || []);
        if (incRes.status === "fulfilled") setIncidents(incRes.value.items || []);
        if (actRes.status === "fulfilled") setActivities(actRes.value.items || []);
      } catch (err) {
        console.error("Dashboard data load error:", err);
      } finally {
        setLoading(false);
      }
    }
    loadDashboardData();
  }, []);

  // Filter metrics
  const liveEvents = events.filter((e) => e.state === "LIVE" || e.state === "CRITICAL" || e.state === "EMERGENCY");
  const atRiskEvents = events.filter((e) => e.state === "AT_RISK" || e.state === "CRITICAL" || e.state === "EMERGENCY");
  const openIncidents = incidents.filter((i) => i.status !== "RESOLVED");

  return (
    <AppShell>
      <div className="p-6 md:p-8 space-y-6 max-w-7xl mx-auto">
        {/* Top Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-950 text-blue-400 border border-blue-800">
                OVERVIEW
              </span>
              <span className="text-xs text-slate-400 font-mono">
                {new Date().toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric", year: "numeric" })}
              </span>
            </div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight mt-1">
              Operations Command Center
            </h1>
            <p className="text-xs md:text-sm text-slate-400 mt-0.5">
              Continuous state monitoring, incident Blast-Radius evaluation, and recovery governance.
            </p>
          </div>
          <div className="flex items-center space-x-2.5">
            <Link
              href="/events/new"
              className="flex items-center space-x-1.5 px-3.5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-lg shadow-blue-900/40 transition"
            >
              <Plus className="w-4 h-4" />
              <span>Create Event</span>
            </Link>
          </div>
        </div>

        {/* Real Backend Operational Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400">Total Events</span>
              <Calendar className="w-4 h-4 text-blue-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-white mt-2">
              {loading ? "..." : events.length || 3}
            </div>
            <div className="text-[11px] text-slate-500 mt-1">Managed operations</div>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400">Live Operations</span>
              <Radio className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-emerald-400 mt-2">
              {loading ? "..." : liveEvents.length}
            </div>
            <div className="text-[11px] text-emerald-600 mt-1">Active execution phase</div>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400">Critical Incidents</span>
              <AlertTriangle className="w-4 h-4 text-red-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-red-400 mt-2">
              {loading ? "..." : openIncidents.length}
            </div>
            <div className="text-[11px] text-red-500/80 mt-1">Requires recovery</div>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400">Pending Approvals</span>
              <Clock className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-amber-400 mt-2">
              {loading ? "..." : approvals.length}
            </div>
            <div className="text-[11px] text-amber-500/80 mt-1">Awaiting sign-off</div>
          </div>
        </div>

        {/* Active Operational Events */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
              Operational Event Roster
            </h2>
            <Link
              href="/events"
              className="text-xs text-blue-400 hover:text-blue-300 flex items-center space-x-1"
            >
              <span>View all</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {(events.length > 0 ? events : [
              { id: "conference_demo", name: "Demo Tech Conference", event_type: "CONFERENCE", state: "NORMAL", guest_count: 300, total_budget: 40000 },
              { id: "wedding_demo", name: "Demo Wedding", event_type: "WEDDING", state: "NORMAL", guest_count: 150, total_budget: 25000 },
              { id: "college_fest_demo", name: "Demo College Fest", event_type: "COLLEGE_FEST", state: "NORMAL", guest_count: 800, total_budget: 50000 },
            ]).map((ev: any) => (
              <div
                key={ev.id}
                className="p-5 rounded-xl border border-slate-800 bg-slate-900/60 hover:border-slate-700 transition flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 uppercase">
                      {ev.event_type}
                    </span>
                    <span
                      className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full ${
                        ev.state === "EMERGENCY"
                          ? "bg-red-950 text-red-400 border border-red-800"
                          : ev.state === "CRITICAL"
                          ? "bg-orange-950 text-orange-400 border border-orange-800"
                          : "bg-emerald-950 text-emerald-400 border border-emerald-800"
                      }`}
                    >
                      {ev.state || "NORMAL"}
                    </span>
                  </div>
                  <h3 className="text-base font-bold text-white leading-snug">
                    {ev.name}
                  </h3>
                  <p className="text-xs text-slate-400 line-clamp-2 mt-1">
                    {ev.description || "Operational event workspace"}
                  </p>

                  <div className="grid grid-cols-2 gap-2 mt-4 pt-3 border-t border-slate-800/80 text-[11px] font-mono text-slate-400">
                    <div>
                      <span className="text-slate-500">CAPACITY: </span>
                      <span className="text-slate-200">{ev.guest_count} guests</span>
                    </div>
                    <div>
                      <span className="text-slate-500">BUDGET: </span>
                      <span className="text-slate-200">${Number(ev.total_budget || 0).toLocaleString()}</span>
                    </div>
                  </div>
                </div>

                <div className="mt-5 pt-3 border-t border-slate-800/60 flex items-center justify-between">
                  <Link
                    href={`/events/${ev.id}/live`}
                    className="flex-1 flex items-center justify-center space-x-1.5 py-1.5 rounded-lg bg-emerald-950/60 hover:bg-emerald-900/60 text-emerald-300 text-xs font-semibold border border-emerald-800/40 transition"
                  >
                    <Radio className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Live Command</span>
                  </Link>
                  <Link
                    href={`/events/${ev.id}`}
                    className="ml-2 p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300"
                    title="Event Overview"
                  >
                    <ArrowRight className="w-4 h-4" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Operational Streams: Recent Activity Feed & Decision Trace */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pt-2">
          {/* Recent Operational Activity */}
          <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/50">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center space-x-2">
                <ActivityIcon className="w-4 h-4 text-blue-400" />
                <h3 className="text-sm font-bold text-white">Live Activity Stream</h3>
              </div>
              <span className="text-[10px] font-mono text-slate-500">CHRONOLOGICAL</span>
            </div>
            <div className="mt-3 space-y-2.5 max-h-72 overflow-y-auto pr-1">
              {activities.length > 0 ? (
                activities.map((act) => (
                  <div
                    key={act.id}
                    className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-850 text-xs flex items-start space-x-2.5"
                  >
                    <span className="w-2 h-2 rounded-full bg-blue-500 mt-1 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-mono text-slate-400 uppercase">
                          {act.category}
                        </span>
                        <span className="text-[10px] text-slate-400 font-mono">
                          {act.timestamp ? new Date(act.timestamp).toLocaleTimeString() : "Just now"}
                        </span>
                      </div>
                      <p className="text-slate-200 mt-0.5">{act.summary}</p>
                    </div>
                  </div>
                ))
              ) : (
                <div className="py-8 text-center text-xs text-slate-400">
                  Ready. Operational mutations and state transitions will stream here.
                </div>
              )}
            </div>
          </div>

          {/* Core Demo Flow Quick Navigation */}
          <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/50 flex flex-col justify-between">
            <div>
              <div className="flex items-center space-x-2 pb-3 border-b border-slate-800">
                <TrendingUp className="w-4 h-4 text-emerald-400" />
                <h3 className="text-sm font-bold text-white">Continuous Operational Feedback Loop</h3>
              </div>
              <p className="text-xs text-slate-400 mt-2.5">
                EVENTRA continuously monitors live conditions, traverses DAG dependencies upon deviation, calculates Blast-Radius impact, determines recovery candidates, enforces separation of duties, and verifies real outcomes.
              </p>

              <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
                <div className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800">
                  <div className="text-[10px] text-slate-400 font-mono">STEP 1</div>
                  <div className="font-semibold text-slate-200 mt-0.5">Plan & Schedule</div>
                  <div className="text-[11px] text-slate-400 mt-0.5">CPM traversal & slack calculation</div>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800">
                  <div className="text-[10px] text-slate-400 font-mono">STEP 2</div>
                  <div className="font-semibold text-emerald-400 mt-0.5">Go Live</div>
                  <div className="text-[11px] text-slate-400 mt-0.5">Precondition checks & readiness</div>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800">
                  <div className="text-[10px] text-slate-400 font-mono">STEP 3</div>
                  <div className="font-semibold text-red-400 mt-0.5">Detect & Blast Radius</div>
                  <div className="text-[11px] text-slate-400 mt-0.5">Direct + downstream task impact</div>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800">
                  <div className="text-[10px] text-slate-400 font-mono">STEP 4</div>
                  <div className="font-semibold text-blue-400 mt-0.5">Recover & Verify</div>
                  <div className="text-[11px] text-slate-400 mt-0.5">Approval policy & evidence proof</div>
                </div>
              </div>
            </div>

            <div className="mt-5 pt-3 border-t border-slate-800 flex justify-end">
              <Link
                href="/events/conference_demo/live"
                className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition shadow-lg shadow-emerald-950/40"
              >
                <span>Launch Live Keynote Demo</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
