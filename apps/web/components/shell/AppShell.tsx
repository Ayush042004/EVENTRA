"use client";

import { ReactNode, useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { DesktopSidebar } from "./DesktopSidebar";
import { useOperator } from "../../stores/uiStore";
import { useLiveState } from "../../hooks/useLiveState";
import { useApprovals } from "../../hooks/useApprovals";
import { useIncidents } from "../../hooks/useIncidents";
import {
  ShieldAlert,
  Zap,
  CheckCircle2,
  Clock,
  Radio,
  UserCheck,
  ChevronDown,
  X,
  Play,
  RotateCcw,
  Bot,
} from "lucide-react";
import Link from "next/link";
import { OperationsAgentDrawer } from "../operations/OperationsAgentDrawer";

export function AppShell({ children }: { children: ReactNode }) {
  const params = useParams();
  const router = useRouter();
  const eventId = (params?.eventId as string) || "conference_demo";

  const { activeProfile, changeOperator, profiles } = useOperator();
  const { liveState } = useLiveState(eventId);
  const { pendingCount } = useApprovals(eventId);
  const { incidents, reportIncident } = useIncidents(eventId);

  const [isOperatorMenuOpen, setIsOperatorMenuOpen] = useState(false);
  const [isDemoModalOpen, setIsDemoModalOpen] = useState(false);
  const [isAgentDrawerOpen, setIsAgentDrawerOpen] = useState(false);
  const [injecting, setInjecting] = useState(false);
  const [injectResult, setInjectResult] = useState<string | null>(null);

  const openIncidentsCount = incidents.filter(
    (i) => i.status !== "RESOLVED"
  ).length;

  const operationalState = (liveState?.lifecycle_state === "EMERGENCY"
    ? "EMERGENCY"
    : liveState?.lifecycle_state === "INCIDENT"
    ? "CRITICAL"
    : "NORMAL") as string;

  // 1-Click Primary Demo Injector: Vendor No-Show
  const handleInjectVendorNoShow = async () => {
    setInjecting(true);
    setInjectResult(null);
    try {
      // Find an AV or critical path task
      const avTask = liveState?.task_progress?.find((t) => 
        t.task_name.toLowerCase().includes("audio") || 
        t.task_name.toLowerCase().includes("av") || 
        t.task_name.toLowerCase().includes("video")
      ) || liveState?.task_progress?.find((t) => t.is_critical_path) || liveState?.task_progress?.[0];

      const res = await reportIncident({
        incident_type: "VENDOR_NO_SHOW",
        severity: "CRITICAL",
        title: "Critical AV Provider No-Show (Beamline AV)",
        description:
          "Audio/Visual provider Beamline AV & Displays has failed to check in 60 minutes prior to keynote. Phone unreachable.",
        related_task_id: avTask?.task_id || undefined,
        related_vendor_id: "vnd-003-blr-av",
        evidence_metadata: {
          delay_minutes: 45,
          call_time_missed_minutes: 45,
          phone_attempts: 4,
          provider_eta_minutes: { "vnd-012-sea-av": 25 },
        },
      });

      setInjectResult(`Incident logged: "${res?.title}". State elevated.`);
      setIsDemoModalOpen(false);
      // Route immediately to the incident triage or recovery screen
      router.push(`/events/${eventId}/incidents`);
    } catch (err: any) {
      setInjectResult(`Injection failed: ${err?.message || "Unknown error"}`);
    } finally {
      setInjecting(false);
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#070b12] text-slate-100 font-sans">
      {/* Desktop Sidebar */}
      <DesktopSidebar />

      {/* Main Command Center Wrapper */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Telemetry & Control Bar */}
        <header className="h-14 border-b border-slate-800 bg-[#090d16]/95 backdrop-blur-md px-4 flex items-center justify-between z-30 flex-shrink-0">
          {/* Left: Operational State Telemetry */}
          <div className="flex items-center space-x-3 min-w-0">
            {/* Operational State Pill */}
            <div className="flex items-center space-x-1.5">
              <span className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider">
                STATE:
              </span>
              {operationalState === "EMERGENCY" ? (
                <span className="flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full bg-red-950/80 border border-red-500 text-red-400 text-xs font-bold tracking-wide animate-radar">
                  <span className="w-2 h-2 rounded-full bg-red-500" />
                  <span>EMERGENCY</span>
                </span>
              ) : operationalState === "CRITICAL" ? (
                <span className="flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full bg-orange-950/80 border border-orange-500 text-orange-400 text-xs font-bold tracking-wide">
                  <span className="w-2 h-2 rounded-full bg-orange-500 animate-pulse" />
                  <span>CRITICAL</span>
                </span>
              ) : (
                <span className="flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full bg-emerald-950/60 border border-emerald-500/50 text-emerald-400 text-xs font-semibold">
                  <span className="w-2 h-2 rounded-full bg-emerald-500" />
                  <span>NORMAL</span>
                </span>
              )}
            </div>

            {/* Lifecycle State Pill */}
            <div className="hidden sm:flex items-center space-x-1.5 pl-2 border-l border-slate-800">
              <span className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider">
                LIFECYCLE:
              </span>
              <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-[11px] font-mono text-slate-300">
                {liveState?.lifecycle_state || "PLANNED"}
              </span>
            </div>

            {/* Active Incidents Pill */}
            {openIncidentsCount > 0 && (
              <Link
                href={`/events/${eventId}/incidents`}
                className="flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full bg-red-950/60 border border-red-800 hover:border-red-600 text-red-300 text-xs font-medium transition"
              >
                <ShieldAlert className="w-3.5 h-3.5 text-red-400" />
                <span>{openIncidentsCount} Incident{openIncidentsCount > 1 ? "s" : ""}</span>
              </Link>
            )}

            {/* Pending Approvals Pill */}
            {pendingCount > 0 && (
              <Link
                href={`/events/${eventId}/approvals`}
                className="flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full bg-amber-950/60 border border-amber-800 hover:border-amber-600 text-amber-300 text-xs font-medium transition"
              >
                <Clock className="w-3.5 h-3.5 text-amber-400" />
                <span>{pendingCount} Pending Approval{pendingCount > 1 ? "s" : ""}</span>
              </Link>
            )}
          </div>

          {/* Right: Agent, Demo Injector & Operator Profile Switcher */}
          <div className="flex items-center space-x-2.5 flex-shrink-0">
            {/* Autonomous Operations Agent Trigger */}
            <button
              onClick={() => setIsAgentDrawerOpen(true)}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 border border-blue-500/30 text-xs font-semibold tracking-wide transition shadow-sm"
              title="Open Autonomous Event Operations Agent"
            >
              <Bot className="w-3.5 h-3.5 text-blue-400" />
              <span className="hidden md:inline">OPS AGENT</span>
            </button>

            {/* Quick Demo Trigger */}
            <button
              onClick={() => setIsDemoModalOpen(true)}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-slate-950 text-xs font-bold tracking-wide shadow-md transition"
              title="Open Hackathon Demo Injector"
            >
              <Zap className="w-3.5 h-3.5 fill-current" />
              <span className="hidden md:inline">DEMO CONTROL</span>
            </button>

            {/* Operator Identity Dropdown */}
            <div className="relative">
              <button
                onClick={() => setIsOperatorMenuOpen(!isOperatorMenuOpen)}
                className="flex items-center space-x-2 px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-xs transition"
              >
                <div className="w-5 h-5 rounded-full bg-blue-600 flex items-center justify-center text-[10px] font-bold text-white">
                  {activeProfile.name[0]}
                </div>
                <div className="text-left hidden lg:block">
                  <div className="text-xs font-semibold text-slate-200 leading-tight">
                    {activeProfile.name.split(" ")[0]}
                  </div>
                  <div className="text-[9px] font-mono text-slate-400 leading-none">
                    {activeProfile.role}
                  </div>
                </div>
                <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
              </button>

              {isOperatorMenuOpen && (
                <div className="absolute right-0 mt-1.5 w-64 z-50 rounded-lg bg-slate-900 border border-slate-700 shadow-2xl p-1.5 backdrop-blur-md">
                  <div className="px-2 py-1.5 border-b border-slate-800 mb-1">
                    <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                      Active Operator Persona
                    </div>
                    <div className="text-[11px] text-slate-400 mt-0.5">
                      Switching persona tests RBAC & separation of duties.
                    </div>
                  </div>
                  <div className="space-y-1">
                    {profiles.map((p) => (
                      <button
                        key={p.id}
                        onClick={() => {
                          changeOperator(p.id);
                          setIsOperatorMenuOpen(false);
                        }}
                        className={`w-full text-left p-2 rounded text-xs transition ${
                          p.id === activeProfile.id
                            ? "bg-blue-600/20 text-blue-300 font-semibold border border-blue-600/30"
                            : "hover:bg-slate-800 text-slate-300"
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-medium">{p.name}</span>
                          <span className="text-[9px] font-mono px-1 rounded bg-slate-800 text-slate-400">
                            {p.role}
                          </span>
                        </div>
                        <div className="text-[10px] text-slate-400 mt-0.5 line-clamp-1">
                          {p.description}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto bg-[#070b12] bg-grid-pattern relative">
          {children}
        </main>
      </div>

      {/* Demo Scenario Modal */}
      {isDemoModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="max-w-lg w-full rounded-xl bg-slate-900 border border-slate-700 shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            {/* Modal Header */}
            <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/70">
              <div className="flex items-center space-x-2.5">
                <div className="p-2 rounded-lg bg-amber-500/20 text-amber-400 border border-amber-500/30">
                  <Zap className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-100">
                    EVENTRA Operational Demo Control
                  </h3>
                  <p className="text-xs text-slate-400">
                    Inject authentic incidents into the live engine pipeline
                  </p>
                </div>
              </div>
              <button
                onClick={() => setIsDemoModalOpen(false)}
                className="text-slate-400 hover:text-slate-200 p-1"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-5 space-y-4">
              <div className="p-3 rounded-lg bg-amber-950/20 border border-amber-900/40 text-xs text-amber-200">
                <span className="font-bold">Canonical Test Scenario:</span> Injects an authentic <code>VENDOR_NO_SHOW</code> incident for the active keynote AV vendor. The engine calculates impact, escalates risk to EMERGENCY, generates recovery alternatives, and routes required approvals.
              </div>

              <div className="space-y-2">
                <button
                  onClick={handleInjectVendorNoShow}
                  disabled={injecting}
                  className="w-full flex items-center justify-between p-3.5 rounded-lg bg-red-600 hover:bg-red-500 text-white font-semibold text-xs transition shadow-lg shadow-red-900/40 disabled:opacity-50"
                >
                  <div className="flex items-center space-x-2.5">
                    <Play className="w-4 h-4 fill-current" />
                    <div className="text-left">
                      <div className="font-bold">1. Inject Vendor No-Show Incident</div>
                      <div className="text-[11px] text-red-200 font-normal">
                        Primary Keynote AV provider fails to check in (60m to launch)
                      </div>
                    </div>
                  </div>
                  <span className="text-[10px] font-mono uppercase bg-red-950/60 px-2 py-1 rounded border border-red-400">
                    {injecting ? "INJECTING..." : "EXECUTE"}
                  </span>
                </button>
              </div>

              {injectResult && (
                <div className="p-3 rounded bg-slate-950 border border-slate-800 text-xs text-slate-300 font-mono">
                  {injectResult}
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-3 border-t border-slate-800 bg-slate-950/50 flex justify-end">
              <button
                onClick={() => setIsDemoModalOpen(false)}
                className="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Operations Agent Autonomous Drawer */}
      <OperationsAgentDrawer
        isOpen={isAgentDrawerOpen}
        onClose={() => setIsAgentDrawerOpen(false)}
        eventId={eventId}
      />
    </div>
  );
}
