"use client";

import { useParams } from "next/navigation";
import { useEvent } from "../../../../hooks/useEvent";
import {
  Settings,
  ShieldAlert,
  Target,
  Clock,
  DollarSign,
  Users,
  CheckCircle2,
  FileText,
  Building,
} from "lucide-react";
import Link from "next/link";

export default function EventSetupPage() {
  const params = useParams();
  const eventId = params?.eventId as string;

  const { event, specification, isLoading, error } = useEvent(eventId);

  return (
    <div className="p-6 md:p-8 max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-blue-950 text-blue-400 border border-blue-800 font-bold">
            PHASE 2 DOMAIN SPECIFICATION
          </span>
          <h1 className="text-2xl md:text-3xl font-extrabold text-white mt-1">
            Operational Specification & Baselines
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Normalized constraints, business objectives, and baseline requirements compiled by the Domain Intelligence engine.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Link
            href={`/events/${eventId}/plan`}
            className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-lg shadow-blue-900/40 transition"
          >
            Go to Planning Engine →
          </Link>
        </div>
      </div>

      {isLoading && (
        <div className="p-12 text-center text-xs text-slate-500 font-mono">
          Loading domain specification from backend...
        </div>
      )}

      {specification && (
        <div className="space-y-6">
          {/* Core Metadata Grid */}
          <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/60">
            <h2 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-4">
              Event Identity & Global Parameters
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs font-mono">
              <div className="p-3 rounded-lg bg-slate-950/70 border border-slate-800">
                <span className="text-[10px] text-slate-500 block">EVENT DOMAIN</span>
                <span className="font-bold text-blue-400">{specification.event_type}</span>
              </div>
              <div className="p-3 rounded-lg bg-slate-950/70 border border-slate-800">
                <span className="text-[10px] text-slate-500 block">CAPACITY REQUIREMENT</span>
                <span className="font-bold text-slate-200">{specification.guest_count} Attendees</span>
              </div>
              <div className="p-3 rounded-lg bg-slate-950/70 border border-slate-800">
                <span className="text-[10px] text-slate-500 block">TOTAL BUDGET CAP</span>
                <span className="font-bold text-emerald-400">${Number(specification.total_budget || 0).toLocaleString()}</span>
              </div>
              <div className="p-3 rounded-lg bg-slate-950/70 border border-slate-800">
                <span className="text-[10px] text-slate-500 block">LIFECYCLE STATUS</span>
                <span className="font-bold text-slate-300">{specification.status || "SPECIFIED"}</span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Objectives */}
            <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/60 space-y-3">
              <div className="flex items-center space-x-2 pb-2 border-b border-slate-800">
                <Target className="w-4 h-4 text-emerald-400" />
                <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                  Operational Objectives ({specification.objectives?.length || 0})
                </h3>
              </div>
              <div className="space-y-2">
                {specification.objectives?.map((obj, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-lg bg-slate-950/70 border border-slate-850 flex items-start justify-between"
                  >
                    <div>
                      <div className="text-xs font-semibold text-slate-200">{obj.title}</div>
                      {obj.description && (
                        <div className="text-[11px] text-slate-400 mt-0.5">{obj.description}</div>
                      )}
                    </div>
                    <span
                      className={`text-[9px] font-mono px-2 py-0.5 rounded font-bold uppercase ${
                        obj.priority === "CRITICAL"
                          ? "bg-red-950 text-red-400 border border-red-800"
                          : "bg-blue-950 text-blue-400 border border-blue-800"
                      }`}
                    >
                      {obj.priority}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Governing Constraints */}
            <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/60 space-y-3">
              <div className="flex items-center space-x-2 pb-2 border-b border-slate-800">
                <ShieldAlert className="w-4 h-4 text-amber-400" />
                <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                  Operational Constraints ({specification.constraints?.length || 0})
                </h3>
              </div>
              <div className="space-y-2">
                {specification.constraints?.map((c, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-lg bg-slate-950/70 border border-slate-850 text-xs"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono font-bold text-amber-400">
                        {c.constraint_type}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-300 mt-1">
                      {c.description || JSON.stringify(c.parameters)}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Provider Categories Required */}
          <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/60">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3">
              Authoritative Vendor Categories Required
            </h3>
            <div className="flex flex-wrap gap-2">
              {specification.provider_categories?.map((cat, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono text-slate-300 uppercase"
                >
                  {cat}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
