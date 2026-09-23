"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import {
  AlertTriangle,
  ShieldAlert,
  Flame,
  ArrowRight,
  RefreshCw,
  Plus,
  Layers,
  Target,
  Sliders,
  CheckCircle,
  ExternalLink,
  ChevronRight,
  X,
  FileText,
} from "lucide-react";
import {
  listIncidents,
  getIncident,
  createIncident,
  recalculateIncident,
  resolveIncident,
} from "../../../../lib/api/incidents";
import type {
  IncidentResponse,
  IncidentCreate,
  IncidentType,
  IncidentSeverity,
  ImpactResultResponse,
  RiskResultResponse,
} from "../../../../types/api";

export default function IncidentsPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  const eventId = params.eventId as string;
  const initialIncidentId = searchParams.get("incidentId");

  const [incidents, setIncidents] = useState<IncidentResponse[]>([]);
  const [selectedIncident, setSelectedIncident] = useState<IncidentResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [recalculating, setRecalculating] = useState(false);
  const [resolving, setResolving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // New incident modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newType, setNewType] = useState<IncidentType>("VENDOR_NO_SHOW");
  const [newSeverity, setNewSeverity] = useState<IncidentSeverity>("CRITICAL");
  const [newDescription, setNewDescription] = useState("");
  const [creating, setCreating] = useState(false);

  // Resolve modal
  const [showResolveModal, setShowResolveModal] = useState(false);
  const [resolutionNotes, setResolutionNotes] = useState("");

  async function loadIncidents() {
    try {
      setLoading(true);
      setError(null);
      const res = await listIncidents(eventId);
      setIncidents(res.items);
      if (res.items.length > 0) {
        if (initialIncidentId) {
          const match = res.items.find((i) => i.id === initialIncidentId);
          setSelectedIncident(match || res.items[0]);
        } else if (!selectedIncident) {
          setSelectedIncident(res.items[0]);
        }
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load incidents";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (eventId) {
      loadIncidents();
    }
  }, [eventId]);

  async function handleSelectIncident(inc: IncidentResponse) {
    try {
      const full = await getIncident(eventId, inc.id);
      setSelectedIncident(full);
    } catch {
      setSelectedIncident(inc);
    }
  }

  async function handleRecalculate() {
    if (!selectedIncident) return;
    try {
      setRecalculating(true);
      const updated = await recalculateIncident(eventId, selectedIncident.id);
      setSelectedIncident(updated);
      await loadIncidents();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to recalculate incident";
      alert(msg);
    } finally {
      setRecalculating(false);
    }
  }

  async function handleResolve() {
    if (!selectedIncident) return;
    try {
      setResolving(true);
      const res = await resolveIncident(eventId, selectedIncident.id, resolutionNotes);
      setSelectedIncident(res);
      setShowResolveModal(false);
      setResolutionNotes("");
      await loadIncidents();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to resolve incident";
      alert(msg);
    } finally {
      setResolving(false);
    }
  }

  async function handleCreateIncident(e: React.FormEvent) {
    e.preventDefault();
    if (!newTitle.trim()) return;
    try {
      setCreating(true);
      const created = await createIncident(eventId, {
        incident_type: newType,
        title: newTitle,
        severity: newSeverity,
        description: newDescription,
        occurred_at: new Date().toISOString(),
      });
      setShowCreateModal(false);
      setNewTitle("");
      setNewDescription("");
      await loadIncidents();
      setSelectedIncident(created);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to log incident";
      alert(msg);
    } finally {
      setCreating(false);
    }
  }

  const impact = selectedIncident?.impact_result as ImpactResultResponse | undefined;
  const risk = selectedIncident?.risk_result as RiskResultResponse | undefined;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border/40 pb-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
              <ShieldAlert className="w-6 h-6 text-rose-500" />
              Incident, Impact & Risk Analysis Center
            </h1>
            {selectedIncident && (
              <span
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider ${
                  selectedIncident.severity === "CRITICAL" ||
                  selectedIncident.severity === "EMERGENCY"
                    ? "bg-rose-500/20 text-rose-400 border border-rose-500/30 animate-pulse"
                    : "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                }`}
              >
                {selectedIncident.severity}
              </span>
            )}
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            Algorithmic blast-radius DAG graph traversal, multi-factor risk quantification, and downstream ripple assessment.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadIncidents}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-border/60 hover:bg-card/60 text-muted-foreground hover:text-foreground transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-rose-600 hover:bg-rose-500 text-white shadow-sm transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            Log Incident
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl border border-rose-500/30 bg-rose-500/5 text-rose-300 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Grid: Incident Selector Column + Deep Blast Radius / Risk Scorecard */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Incident List Roster */}
        <div className="lg:col-span-4 space-y-3">
          <div className="flex items-center justify-between text-xs font-semibold text-muted-foreground uppercase tracking-wider px-1">
            <span>Logged Incidents ({incidents.length})</span>
          </div>

          {incidents.length === 0 ? (
            <div className="p-6 rounded-xl border border-border/50 bg-card/30 text-center text-xs text-muted-foreground space-y-3">
              <CheckCircle className="w-8 h-8 text-emerald-400/50 mx-auto" />
              <p>No active or historical incidents recorded for this event.</p>
              <button
                onClick={() => setShowCreateModal(true)}
                className="px-3 py-1.5 rounded-lg bg-secondary text-foreground text-xs font-medium hover:bg-secondary/80"
              >
                Log an Incident
              </button>
            </div>
          ) : (
            <div className="space-y-2">
              {incidents.map((inc) => {
                const isSelected = selectedIncident?.id === inc.id;
                return (
                  <div
                    key={inc.id}
                    onClick={() => handleSelectIncident(inc)}
                    className={`p-3.5 rounded-xl border cursor-pointer transition-all space-y-2 ${
                      isSelected
                        ? "bg-card border-rose-500/50 shadow-md ring-1 ring-rose-500/20"
                        : "bg-card/40 border-border/40 hover:bg-card/70 hover:border-border/70"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="space-y-0.5">
                        <span className="text-[10px] font-mono uppercase text-muted-foreground">
                          {inc.incident_type}
                        </span>
                        <h3 className="text-xs font-bold text-foreground line-clamp-1">
                          {inc.title}
                        </h3>
                      </div>
                      <span
                        className={`px-1.5 py-0.5 rounded text-[10px] font-bold shrink-0 ${
                          inc.severity === "CRITICAL"
                            ? "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                            : "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                        }`}
                      >
                        {inc.severity}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-[11px] text-muted-foreground pt-1 border-t border-border/20">
                      <span>Status: {inc.status}</span>
                      <span>
                        {new Date(inc.detected_at).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Selected Incident Telemetry & Blast Radius */}
        <div className="lg:col-span-8 space-y-6">
          {selectedIncident ? (
            <>
              {/* Incident Header Card with Actions */}
              <div className="p-5 rounded-xl border border-border/60 bg-card/40 backdrop-blur-sm space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-rose-500/10 text-rose-400 border border-rose-500/20">
                        {selectedIncident.incident_type}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        Detected: {new Date(selectedIncident.detected_at).toLocaleString()}
                      </span>
                    </div>
                    <h2 className="text-lg font-bold text-foreground">
                      {selectedIncident.title}
                    </h2>
                    {selectedIncident.description && (
                      <p className="text-xs text-muted-foreground">
                        {selectedIncident.description}
                      </p>
                    )}
                  </div>

                  <div className="flex flex-wrap items-center gap-2 shrink-0">
                    <button
                      onClick={handleRecalculate}
                      disabled={recalculating}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-border/60 hover:bg-card text-muted-foreground hover:text-foreground transition-colors"
                    >
                      <RefreshCw
                        className={`w-3.5 h-3.5 ${recalculating ? "animate-spin" : ""}`}
                      />
                      Recalculate
                    </button>

                    {selectedIncident.status !== "RESOLVED" && (
                      <button
                        onClick={() => setShowResolveModal(true)}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-border/60 hover:bg-emerald-500/10 hover:border-emerald-500/30 hover:text-emerald-400 text-muted-foreground transition-colors"
                      >
                        <CheckCircle className="w-3.5 h-3.5" />
                        Resolve
                      </button>
                    )}

                    {/* DIRECT BRIDGE TO RECOVERY */}
                    <button
                      onClick={() =>
                        router.push(
                          `/events/${eventId}/recovery?incidentId=${selectedIncident.id}`
                        )
                      }
                      className="inline-flex items-center gap-2 px-4 py-1.5 text-xs font-bold rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground shadow-sm transition-colors"
                    >
                      Generate Recovery Options
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>

              {/* Multi-Factor Risk Scorecard */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm flex flex-col justify-between">
                  <div className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                    <Flame className="w-3.5 h-3.5 text-rose-400" />
                    Composite Risk Score
                  </div>
                  <div className="flex items-baseline gap-2 mt-2">
                    <span
                      className={`text-3xl font-extrabold tracking-tight ${
                        (risk?.score || 0) > 60
                          ? "text-rose-400"
                          : (risk?.score || 0) > 30
                          ? "text-amber-400"
                          : "text-emerald-400"
                      }`}
                    >
                      {(risk?.score || 0).toFixed(0)}
                    </span>
                    <span className="text-xs text-muted-foreground font-mono">/ 100</span>
                    <span className="ml-auto px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/10 text-rose-300 border border-rose-500/20">
                      {risk?.level || "CALCULATED"}
                    </span>
                  </div>
                  <div className="text-[11px] text-muted-foreground mt-2">
                    Target State:{" "}
                    <span className="font-semibold text-rose-300">
                      {risk?.target_event_state || "CRITICAL"}
                    </span>
                  </div>
                </div>

                <div className="p-4 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm flex flex-col justify-between">
                  <div className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                    <Layers className="w-3.5 h-3.5 text-amber-400" />
                    Blast Radius Depth
                  </div>
                  <div className="text-3xl font-extrabold tracking-tight text-amber-400 mt-2">
                    {impact?.dependency_depth ?? 0}{" "}
                    <span className="text-xs font-normal text-muted-foreground">
                      DAG levels
                    </span>
                  </div>
                  <div className="text-[11px] text-muted-foreground mt-2">
                    Downstream ripple cascades
                  </div>
                </div>

                <div className="p-4 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm flex flex-col justify-between">
                  <div className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                    <Target className="w-3.5 h-3.5 text-blue-400" />
                    Threatened Objectives
                  </div>
                  <div className="text-3xl font-extrabold tracking-tight text-blue-400 mt-2">
                    {risk?.affected_objectives?.length ?? 0}
                  </div>
                  <div className="text-[11px] text-muted-foreground mt-2 truncate">
                    {risk?.affected_objectives?.join(", ") || "No objectives breached"}
                  </div>
                </div>
              </div>

              {/* Blast-Radius DAG Task Impact Breakdown */}
              <div className="p-5 rounded-xl border border-border/50 bg-card/30 backdrop-blur-sm space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Layers className="w-4 h-4 text-rose-400" />
                    <h3 className="text-sm font-bold text-foreground">
                      Blast-Radius DAG: Directly & Indirectly Affected Tasks
                    </h3>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {(impact?.directly_affected_tasks?.length || 0) +
                      (impact?.indirectly_affected_tasks?.length || 0)}{" "}
                    Total Impaired Tasks
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Epicenter: Directly Affected */}
                  <div className="p-4 rounded-lg bg-rose-500/5 border border-rose-500/20 space-y-2">
                    <div className="flex items-center justify-between text-xs font-semibold text-rose-300 uppercase tracking-wider">
                      <span>Epicenter (Directly Hit)</span>
                      <span>{impact?.directly_affected_tasks?.length || 0}</span>
                    </div>
                    {impact?.directly_affected_tasks &&
                    impact.directly_affected_tasks.length > 0 ? (
                      <div className="space-y-1.5">
                        {impact.directly_affected_tasks.map((task: any, idx: number) => (
                          <div
                            key={idx}
                            className="p-2 rounded bg-card/70 border border-rose-500/30 text-xs font-medium text-foreground flex items-center justify-between"
                          >
                            <span>{task.name || task.task_name || task.task_id || "Task"}</span>
                            <span className="text-[10px] text-rose-400 font-bold uppercase">
                              Direct
                            </span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-xs text-muted-foreground italic py-2">
                        No direct task attachments
                      </div>
                    )}
                  </div>

                  {/* Ripple: Indirectly Affected (Downstream) */}
                  <div className="p-4 rounded-lg bg-amber-500/5 border border-amber-500/20 space-y-2">
                    <div className="flex items-center justify-between text-xs font-semibold text-amber-300 uppercase tracking-wider">
                      <span>Ripple Cascade (Downstream)</span>
                      <span>{impact?.indirectly_affected_tasks?.length || 0}</span>
                    </div>
                    {impact?.indirectly_affected_tasks &&
                    impact.indirectly_affected_tasks.length > 0 ? (
                      <div className="space-y-1.5">
                        {impact.indirectly_affected_tasks.map(
                          (task: any, idx: number) => (
                            <div
                              key={idx}
                              className="p-2 rounded bg-card/70 border border-amber-500/30 text-xs font-medium text-foreground flex items-center justify-between"
                            >
                              <span>
                                {task.name || task.task_name || task.task_id || "Task"}
                              </span>
                              <span className="text-[10px] text-amber-400 font-bold uppercase">
                                Downstream
                              </span>
                            </div>
                          )
                        )}
                      </div>
                    ) : (
                      <div className="text-xs text-muted-foreground italic py-2">
                        No downstream cascade
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Risk Factors Breakdown Table */}
              {risk?.factors && risk.factors.length > 0 && (
                <div className="rounded-xl border border-border/50 bg-card/30 backdrop-blur-sm overflow-hidden">
                  <div className="p-4 border-b border-border/40 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Sliders className="w-4 h-4 text-primary" />
                      <h3 className="text-sm font-semibold text-foreground">
                        Weighted Risk Evaluation Factors
                      </h3>
                    </div>
                  </div>
                  <div className="divide-y divide-border/30">
                    {risk.factors.map((factor, idx) => (
                      <div
                        key={idx}
                        className="p-3.5 hover:bg-card/40 transition-colors flex items-center justify-between text-xs"
                      >
                        <div className="space-y-0.5">
                          <div className="font-semibold text-foreground">
                            {factor.name}
                          </div>
                          <div className="text-muted-foreground text-[11px]">
                            {factor.description}
                          </div>
                        </div>
                        <div className="flex items-center gap-4 text-right">
                          <div>
                            <div className="text-[10px] text-muted-foreground">Raw</div>
                            <div className="font-mono font-bold text-foreground">
                              {factor.score.toFixed(1)}
                            </div>
                          </div>
                          <div>
                            <div className="text-[10px] text-muted-foreground">Weight</div>
                            <div className="font-mono text-muted-foreground">
                              {(factor.weight * 100).toFixed(0)}%
                            </div>
                          </div>
                          <div>
                            <div className="text-[10px] text-muted-foreground">Weighted</div>
                            <div className="font-mono font-bold text-rose-400">
                              {factor.weighted_score.toFixed(1)}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="p-12 text-center rounded-xl border border-border/50 bg-card/30 text-xs text-muted-foreground">
              Select an incident from the left or log a new incident to view deep blast-radius impact and risk calculations.
            </div>
          )}
        </div>
      </div>

      {/* Log New Incident Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm">
          <form
            onSubmit={handleCreateIncident}
            className="bg-card border border-border/60 rounded-2xl p-6 w-full max-w-lg shadow-2xl space-y-4"
          >
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-base font-bold text-foreground">
                  Log Operational Incident
                </h3>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Submits an anomaly to the backend impact DAG and multi-factor risk engine.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                className="text-muted-foreground hover:text-foreground p-1 rounded-lg"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-muted-foreground mb-1">
                  Incident Type
                </label>
                <select
                  value={newType}
                  onChange={(e) => setNewType(e.target.value as IncidentType)}
                  className="w-full p-2.5 rounded-lg bg-secondary/50 border border-border text-foreground"
                >
                  <option value="VENDOR_NO_SHOW">VENDOR_NO_SHOW</option>
                  <option value="VENDOR_DELAY">VENDOR_DELAY</option>
                  <option value="VENUE_UNAVAILABLE">VENUE_UNAVAILABLE</option>
                  <option value="RESOURCE_SHORTAGE">RESOURCE_SHORTAGE</option>
                  <option value="TASK_FAILURE">TASK_FAILURE</option>
                  <option value="SCHEDULE_BREACH">SCHEDULE_BREACH</option>
                  <option value="BUDGET_OVERRUN">BUDGET_OVERRUN</option>
                  <option value="SAFETY_HAZARD">SAFETY_HAZARD</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-muted-foreground mb-1">
                  Severity
                </label>
                <select
                  value={newSeverity}
                  onChange={(e) => setNewSeverity(e.target.value as IncidentSeverity)}
                  className="w-full p-2.5 rounded-lg bg-secondary/50 border border-border text-foreground"
                >
                  <option value="LOW">LOW</option>
                  <option value="MEDIUM">MEDIUM</option>
                  <option value="HIGH">HIGH</option>
                  <option value="CRITICAL">CRITICAL</option>
                  <option value="EMERGENCY">EMERGENCY</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-muted-foreground mb-1">
                  Title
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Lead Sound Vendor No-Show"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="w-full p-2.5 rounded-lg bg-secondary/50 border border-border text-foreground"
                />
              </div>

              <div>
                <label className="block font-semibold text-muted-foreground mb-1">
                  Description / Evidence
                </label>
                <textarea
                  rows={3}
                  placeholder="Describe operational breakdown and evidence..."
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  className="w-full p-2.5 rounded-lg bg-secondary/50 border border-border text-foreground"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-border/40">
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                className="px-3 py-1.5 text-xs font-medium rounded-lg border border-border/60 hover:bg-card text-muted-foreground"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={creating}
                className="px-4 py-1.5 text-xs font-bold rounded-lg bg-rose-600 hover:bg-rose-500 text-white shadow-sm"
              >
                {creating ? "Submitting..." : "Log & Compute Blast Radius"}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Resolve Incident Modal */}
      {showResolveModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm">
          <div className="bg-card border border-border/60 rounded-2xl p-6 w-full max-w-md shadow-2xl space-y-4">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-base font-bold text-foreground">
                  Resolve Incident
                </h3>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Records formal resolution notes in the immutable audit log.
                </p>
              </div>
              <button
                onClick={() => setShowResolveModal(false)}
                className="text-muted-foreground hover:text-foreground p-1 rounded-lg"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div>
              <label className="block text-xs font-semibold text-muted-foreground mb-1">
                Resolution Notes
              </label>
              <textarea
                rows={3}
                placeholder="Details of corrective action taken..."
                value={resolutionNotes}
                onChange={(e) => setResolutionNotes(e.target.value)}
                className="w-full p-2.5 rounded-lg bg-secondary/50 border border-border text-foreground text-xs"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-border/40">
              <button
                onClick={() => setShowResolveModal(false)}
                className="px-3 py-1.5 text-xs font-medium rounded-lg border border-border/60 hover:bg-card text-muted-foreground"
              >
                Cancel
              </button>
              <button
                onClick={handleResolve}
                disabled={resolving}
                className="px-4 py-1.5 text-xs font-bold rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white shadow-sm"
              >
                {resolving ? "Resolving..." : "Confirm Resolution"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
