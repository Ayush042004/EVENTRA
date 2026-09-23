"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AppShell } from "../../components/shell/AppShell";
import { listEvents } from "../../lib/api/events";
import type { EventResponse } from "../../types/api";
import { Plus, Search, Calendar, Radio, ArrowRight, DollarSign, Users } from "lucide-react";

export default function EventsListPage() {
  const [events, setEvents] = useState<EventResponse[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchEvents() {
      setLoading(true);
      try {
        const res = await listEvents();
        if (res && res.length > 0) {
          setEvents(res);
        } else {
          // Fallback demo events if none created yet
          setEvents([
            {
              id: "conference_demo",
              name: "Demo Tech Conference 2026",
              description: "Flagship annual developer keynote and product launches",
              event_type: "CONFERENCE",
              state: "NORMAL",
              guest_count: 300,
              total_budget: 40000,
              currency: "USD",
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            },
            {
              id: "wedding_demo",
              name: "Demo Horizon Wedding Gala",
              description: "Full service outdoor banquet with staging and catering",
              event_type: "WEDDING",
              state: "NORMAL",
              guest_count: 150,
              total_budget: 25000,
              currency: "USD",
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            },
            {
              id: "college_fest_demo",
              name: "Demo College Spring Fest",
              description: "Multi-stage music, hackathon, and campus food pavilion",
              event_type: "COLLEGE_FEST",
              state: "NORMAL",
              guest_count: 800,
              total_budget: 50000,
              currency: "USD",
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            },
          ]);
        }
      } finally {
        setLoading(false);
      }
    }
    fetchEvents();
  }, []);

  const filtered = events.filter((e) =>
    e.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    e.event_type.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <AppShell>
      <div className="p-6 md:p-8 space-y-6 max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
          <div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
              Event Operations Roster
            </h1>
            <p className="text-xs md:text-sm text-slate-400 mt-1">
              Select an operational workspace to inspect planning, live state, and telemetry.
            </p>
          </div>
          <Link
            href="/events/new"
            className="flex items-center space-x-1.5 px-3.5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-lg shadow-blue-900/40 transition"
          >
            <Plus className="w-4 h-4" />
            <span>Create Event</span>
          </Link>
        </div>

        {/* Filter bar */}
        <div className="flex items-center space-x-3">
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
            <input
              type="text"
              placeholder="Search by event name or domain..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-600"
            />
          </div>
        </div>

        {/* Event Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((ev) => (
            <div
              key={ev.id}
              className="p-5 rounded-xl border border-slate-800 bg-slate-900/70 hover:border-slate-700 transition flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-2.5">
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 uppercase tracking-wider">
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
                <p className="text-xs text-slate-400 line-clamp-2 mt-1.5">
                  {ev.description || "Operational event specification initialized"}
                </p>

                <div className="grid grid-cols-2 gap-2 mt-4 pt-3 border-t border-slate-800/80 text-[11px] font-mono text-slate-400">
                  <div className="flex items-center space-x-1.5">
                    <Users className="w-3.5 h-3.5 text-slate-500" />
                    <span>{ev.guest_count} attendees</span>
                  </div>
                  <div className="flex items-center space-x-1.5">
                    <DollarSign className="w-3.5 h-3.5 text-slate-500" />
                    <span>${Number(ev.total_budget || 0).toLocaleString()}</span>
                  </div>
                </div>
              </div>

              <div className="mt-5 pt-3 border-t border-slate-800/60 flex items-center space-x-2">
                <Link
                  href={`/events/${ev.id}/live`}
                  className="flex-1 flex items-center justify-center space-x-1.5 py-2 rounded-lg bg-emerald-950/60 hover:bg-emerald-900/60 text-emerald-300 text-xs font-semibold border border-emerald-800/40 transition"
                >
                  <Radio className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Command Center</span>
                </Link>
                <Link
                  href={`/events/${ev.id}`}
                  className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
                  title="Event Workspace"
                >
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      </div>
    </AppShell>
  );
}
