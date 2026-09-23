"use client";

import React from "react";
import { useParams } from "next/navigation";
import {
  Users,
  ShieldCheck,
  UserCheck,
  Key,
  Lock,
  CheckCircle,
} from "lucide-react";
import { useUiStore, OPERATOR_PERSONAS } from "../../../../stores/uiStore";

export default function CollaboratorsPage() {
  const params = useParams();
  const eventId = params.eventId as string;
  const { currentOperator, setOperator } = useUiStore();

  const permissionsMap: Record<string, string[]> = {
    anonymous_operator: [
      "AUTHORIZE_HIGH_IMPACT_ACTIONS",
      "OVERRIDE_BUDGET_CEILINGS",
      "APPROVE_RECOVERY_PLANS",
      "TRIGGER_EMERGENCY_CONCLUDE",
      "REASSIGN_VENDORS",
    ],
    collab_alex: [
      "TRANSITION_TASK_STATUS",
      "LOG_OPERATIONAL_INCIDENTS",
      "PROPOSE_RECOVERY_CANDIDATES",
      "DISPATCH_COMMUNICATIONS",
      "VIEW_CPM_SCHEDULE",
    ],
    vendor_apex: [
      "SUBMIT_TASK_PROGRESS",
      "REPORT_ETA_DELAY",
      "RECEIVE_OUTBOUND_MESSAGES",
      "VIEW_ASSIGNED_TASKS",
    ],
    viewer_guest: [
      "READ_ONLY_FLEET_TELEMETRY",
      "VIEW_EVENT_SPECIFICATION",
      "VIEW_AUDIT_LOG",
    ],
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border/40 pb-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
              <Users className="w-6 h-6 text-primary" />
              Operations Team & RBAC Governance
            </h1>
            <span className="font-mono text-[10px] px-2.5 py-0.5 rounded-full bg-secondary text-muted-foreground border border-border/50">
              Separation of Duties
            </span>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            Access control policies, duty segregation matrix, and persona switching for multi-operator hackathon demonstration.
          </p>
        </div>
      </div>

      {/* Active Persona Banner */}
      <div className="p-4 rounded-xl border border-primary/40 bg-primary/5 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-primary/20 border border-primary/30 flex items-center justify-center font-bold text-primary text-sm">
            {currentOperator.name.charAt(0)}
          </div>
          <div>
            <div className="text-xs font-bold text-foreground">
              Active Session: {currentOperator.name}
            </div>
            <div className="text-[11px] text-muted-foreground">
              Role: <strong className="text-primary">{currentOperator.role}</strong> &bull; User ID: <code className="font-mono text-xs">{currentOperator.id}</code>
            </div>
          </div>
        </div>

        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <CheckCircle className="w-3.5 h-3.5" />
          Active In Session Headers
        </span>
      </div>

      {/* Personas Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {OPERATOR_PERSONAS.map((persona) => {
          const isActive = currentOperator.id === persona.id;
          const perms = permissionsMap[persona.id] || [];

          return (
            <div
              key={persona.id}
              className={`p-5 rounded-2xl border transition-all space-y-4 ${
                isActive
                  ? "border-primary/50 bg-card shadow-lg ring-1 ring-primary/20"
                  : "border-border/50 bg-card/40 hover:border-border/70"
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-bold text-foreground">
                      {persona.name}
                    </h3>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-secondary text-secondary-foreground border border-border/50">
                      {persona.role}
                    </span>
                  </div>
                  <div className="text-[11px] font-mono text-muted-foreground">
                    ID: {persona.id}
                  </div>
                </div>

                {isActive ? (
                  <span className="px-2.5 py-0.5 rounded text-[10px] font-bold bg-primary text-primary-foreground">
                    Active Persona
                  </span>
                ) : (
                  <button
                    onClick={() => setOperator(persona)}
                    className="px-3 py-1 rounded-lg text-xs font-semibold border border-border/60 hover:bg-card text-muted-foreground hover:text-foreground transition-colors"
                  >
                    Switch to This Persona
                  </button>
                )}
              </div>

              {/* Permissions list */}
              <div className="space-y-1.5 text-xs pt-2 border-t border-border/30">
                <div className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1">
                  <Key className="w-3 h-3 text-primary" />
                  Granted Policy Scopes:
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {perms.map((p) => (
                    <span
                      key={p}
                      className="px-2 py-0.5 rounded text-[10px] font-mono bg-secondary/60 text-foreground border border-border/40"
                    >
                      {p}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
