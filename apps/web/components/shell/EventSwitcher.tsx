"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { ChevronDown, Calendar, Plus } from "lucide-react";
import { listEvents } from "../../lib/api/events";
import type { EventResponse } from "../../types/api";

const DEMO_EVENTS_FALLBACK: Array<{ id: string; name: string; event_type: string }> = [
  { id: "conference_demo", name: "Tech Launch Keynote 2026", event_type: "CONFERENCE" },
  { id: "wedding_demo", name: "Grand Horizon Wedding", event_type: "WEDDING" },
  { id: "college_fest_demo", name: "North Quad Spring Fest", event_type: "COLLEGE_FEST" },
];

export function EventSwitcher() {
  const router = useRouter();
  const params = useParams();
  const currentEventId = (params?.eventId as string) || "conference_demo";

  const [events, setEvents] = useState<Array<{ id: string; name: string; event_type?: string }>>(DEMO_EVENTS_FALLBACK);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    async function loadEvents() {
      const realEvents = await listEvents();
      if (realEvents && realEvents.length > 0) {
        // Merge with demo fallbacks if not already present
        const combined = [...realEvents];
        for (const demo of DEMO_EVENTS_FALLBACK) {
          if (!combined.some((e) => e.id === demo.id)) {
            combined.push(demo as EventResponse);
          }
        }
        setEvents(combined);
      }
    }
    loadEvents();
  }, []);

  const activeEvent = events.find((e) => e.id === currentEventId) || events[0] || {
    id: currentEventId,
    name: "Active Event",
    event_type: "CONFERENCE",
  };

  const handleSelect = (eventId: string) => {
    setIsOpen(false);
    router.push(`/events/${eventId}/live`);
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-2.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 transition text-left"
      >
        <div className="flex items-center space-x-2.5 min-w-0">
          <div className="p-1.5 rounded bg-blue-950/60 border border-blue-800 text-blue-400">
            <Calendar className="w-4 h-4" />
          </div>
          <div className="truncate">
            <div className="text-xs font-semibold text-slate-200 truncate leading-tight">
              {activeEvent.name}
            </div>
            <div className="text-[10px] text-slate-400 uppercase font-mono mt-0.5">
              {activeEvent.event_type || "EVENT"} • ID: {activeEvent.id.slice(0, 8)}
            </div>
          </div>
        </div>
        <ChevronDown className="w-4 h-4 text-slate-400 ml-2 flex-shrink-0" />
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-1.5 z-50 rounded-lg bg-slate-900 border border-slate-700 shadow-2xl p-1.5 backdrop-blur-md">
          <div className="text-[10px] font-bold text-slate-400 uppercase px-2 py-1 tracking-wider">
            Switch Operational Event
          </div>
          <div className="max-h-56 overflow-y-auto space-y-0.5">
            {events.map((ev) => (
              <button
                key={ev.id}
                onClick={() => handleSelect(ev.id)}
                className={`w-full flex items-center justify-between p-2 rounded text-left text-xs transition ${
                  ev.id === currentEventId
                    ? "bg-blue-600/20 text-blue-300 font-semibold border border-blue-600/40"
                    : "hover:bg-slate-800 text-slate-300"
                }`}
              >
                <span className="truncate">{ev.name}</span>
                <span className="text-[10px] font-mono text-slate-500 ml-2 uppercase">
                  {ev.event_type}
                </span>
              </button>
            ))}
          </div>
          <div className="border-t border-slate-800 mt-1 pt-1">
            <button
              onClick={() => {
                setIsOpen(false);
                router.push("/events/new");
              }}
              className="w-full flex items-center justify-center space-x-1.5 p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Create New Event</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
