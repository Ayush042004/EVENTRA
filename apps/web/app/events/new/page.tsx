"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { AppShell } from "../../../components/shell/AppShell";
import { previewEventSpecification, createEvent } from "../../../lib/api/events";
import { getOperatorId } from "../../../lib/api/client";
import type { EventSpecification, EventSpecificationPreviewRequest } from "../../../types/api";
import {
  Sparkles,
  ArrowRight,
  Calendar,
  DollarSign,
  Users,
  MapPin,
  CheckCircle2,
  AlertCircle,
  FileCheck,
} from "lucide-react";

export default function NewEventPage() {
  const router = useRouter();

  const [formData, setFormData] = useState({
    title: "Global AI Summit 2026",
    description: "Annual keynote and technical conference for live engineering demonstrations.",
    event_type: "CONFERENCE",
    start_time: new Date(Date.now() + 3600 * 1000 * 24).toISOString().slice(0, 16),
    end_time: new Date(Date.now() + 3600 * 1000 * 36).toISOString().slice(0, 16),
    guest_count: 350,
    total_budget: 45000,
    currency: "USD",
    location_name: "Civic Innovation Center",
    location_city: "San Francisco",
  });

  const [previewSpec, setPreviewSpec] = useState<EventSpecification | null>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handlePreview = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoadingPreview(true);
    setError(null);

    const payload: EventSpecificationPreviewRequest = {
      title: formData.title,
      description: formData.description,
      event_type: formData.event_type,
      start_time: new Date(formData.start_time).toISOString(),
      end_time: new Date(formData.end_time).toISOString(),
      guest_count: Number(formData.guest_count),
      total_budget: Number(formData.total_budget),
      currency: formData.currency,
      location: {
        name: formData.location_name,
        city: formData.location_city,
      },
    };

    try {
      const spec = await previewEventSpecification(payload);
      setPreviewSpec(spec);
    } catch (err: any) {
      setError(err?.message || "Failed to generate specification preview");
    } finally {
      setLoadingPreview(false);
    }
  };

  const handleCreate = async () => {
    setCreating(true);
    setError(null);
    try {
      const created = await createEvent({
        owner_id: getOperatorId(),
        name: formData.title,
        description: formData.description,
        event_type: formData.event_type,
        location: `${formData.location_name}, ${formData.location_city}`,
        start_datetime: new Date(formData.start_time).toISOString(),
        end_datetime: new Date(formData.end_time).toISOString(),
        guest_count: Number(formData.guest_count),
        state: "NORMAL",
        total_budget: Number(formData.total_budget),
        currency: formData.currency,
      });

      router.push(`/events/${created.id}/setup`);
    } catch (err: any) {
      setError(err?.message || "Failed to persist event");
    } finally {
      setCreating(false);
    }
  };

  return (
    <AppShell>
      <div className="p-6 md:p-8 max-w-5xl mx-auto space-y-6">
        <div>
          <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-blue-950 text-blue-400 border border-blue-800">
            SPECIFICATION INTAKE
          </span>
          <h1 className="text-2xl md:text-3xl font-extrabold text-white mt-1">
            Initialize Event Specification
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Phase 2 Deterministic Domain Intelligence compilation and baseline preview.
          </p>
        </div>

        {error && (
          <div className="p-3.5 rounded-lg bg-red-950/60 border border-red-800 text-red-300 text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0 text-red-400" />
            <span>{error}</span>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Intake Form */}
          <form
            onSubmit={handlePreview}
            className="p-5 rounded-xl border border-slate-800 bg-slate-900/60 space-y-4"
          >
            <div className="text-xs font-bold text-slate-300 uppercase tracking-wider">
              1. Event Operational Parameters
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">
                Event Name
              </label>
              <input
                type="text"
                required
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-blue-600"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Event Domain
                </label>
                <select
                  value={formData.event_type}
                  onChange={(e) => setFormData({ ...formData, event_type: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-blue-600"
                >
                  <option value="CONFERENCE">CONFERENCE</option>
                  <option value="WEDDING">WEDDING</option>
                  <option value="COLLEGE_FEST">COLLEGE_FEST</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Guest Count (Scalar)
                </label>
                <input
                  type="number"
                  required
                  min={1}
                  value={formData.guest_count}
                  onChange={(e) => setFormData({ ...formData, guest_count: Number(e.target.value) })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-blue-600"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Planned Start
                </label>
                <input
                  type="datetime-local"
                  required
                  value={formData.start_time}
                  onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-blue-600"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Planned End
                </label>
                <input
                  type="datetime-local"
                  required
                  value={formData.end_time}
                  onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-blue-600"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Total Budget Ceiling ($)
                </label>
                <input
                  type="number"
                  required
                  min={0}
                  value={formData.total_budget}
                  onChange={(e) => setFormData({ ...formData, total_budget: Number(e.target.value) })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-blue-600"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Location City
                </label>
                <input
                  type="text"
                  required
                  value={formData.location_city}
                  onChange={(e) => setFormData({ ...formData, location_city: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-blue-600"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">
                Description / Objectives
              </label>
              <textarea
                rows={2}
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-blue-600"
              />
            </div>

            <button
              type="submit"
              disabled={loadingPreview}
              className="w-full py-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-100 text-xs font-bold border border-slate-700 transition flex items-center justify-center space-x-1.5"
            >
              <Sparkles className="w-3.5 h-3.5 text-blue-400" />
              <span>{loadingPreview ? "Compiling Spec..." : "Preview Domain Specification"}</span>
            </button>
          </form>

          {/* Specification Preview Card */}
          <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/60 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <div className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center space-x-1.5">
                  <FileCheck className="w-4 h-4 text-emerald-400" />
                  <span>2. Domain Intelligence Baseline Preview</span>
                </div>
                <span className="text-[10px] font-mono text-slate-500">AUTHORITATIVE</span>
              </div>

              {previewSpec ? (
                <div className="mt-4 space-y-4 max-h-[380px] overflow-y-auto pr-1 text-xs">
                  <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1.5 font-mono text-[11px]">
                    <div className="text-slate-400">
                      DOMAIN: <span className="text-white font-bold">{previewSpec.event_type}</span>
                    </div>
                    <div className="text-slate-400">
                      TASKS MATERIALIZED: <span className="text-emerald-400 font-bold">{previewSpec.tasks?.length || 0}</span>
                    </div>
                    <div className="text-slate-400">
                      DAG EDGES: <span className="text-blue-400 font-bold">{previewSpec.dependencies?.length || 0}</span>
                    </div>
                    <div className="text-slate-400">
                      VENDOR CATEGORIES: <span className="text-slate-200">{previewSpec.provider_categories?.join(", ") || "av, catering"}</span>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-semibold text-slate-300 mb-1.5">Baseline Tasks (Pre-Planning):</h4>
                    <div className="space-y-1">
                      {previewSpec.tasks?.slice(0, 5).map((t, idx) => (
                        <div key={idx} className="p-2 rounded bg-slate-950/80 border border-slate-850 flex items-center justify-between">
                          <span className="text-slate-200 font-medium">{t.name}</span>
                          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 uppercase">
                            {t.priority}
                          </span>
                        </div>
                      ))}
                      {(previewSpec.tasks?.length || 0) > 5 && (
                        <div className="text-[11px] text-slate-500 text-center pt-1 font-mono">
                          + {previewSpec.tasks.length - 5} more domain baseline tasks
                        </div>
                      )}
                    </div>
                  </div>

                  <div>
                    <h4 className="font-semibold text-slate-300 mb-1.5">Governing Constraints:</h4>
                    <div className="space-y-1">
                      {previewSpec.constraints?.map((c, idx) => (
                        <div key={idx} className="p-2 rounded bg-slate-950/80 border border-slate-850 text-[11px]">
                          <span className="font-mono text-amber-400 font-bold">{c.constraint_type}: </span>
                          <span className="text-slate-300">{c.description || JSON.stringify(c.parameters)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="py-24 text-center text-xs text-slate-500">
                  Fill in parameters and click &quot;Preview Domain Specification&quot; to review the compiled baseline before database initialization.
                </div>
              )}
            </div>

            <div className="mt-5 pt-3 border-t border-slate-800 flex justify-end">
              <button
                onClick={handleCreate}
                disabled={creating}
                className="flex items-center space-x-2 px-5 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold shadow-lg shadow-blue-900/40 transition disabled:opacity-50"
              >
                <span>{creating ? "Persisting..." : "Create Event & Initialize"}</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
