"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { getPlan } from "../../../../lib/api/planning";
import type { EventPlan, PlanTaskEntry } from "../../../../types/api";
import { CheckSquare, Search, Filter, Clock, Users } from "lucide-react";

export default function TasksPage() {
  const params = useParams();
  const eventId = params?.eventId as string;

  const [tasks, setTasks] = useState<PlanTaskEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");

  useEffect(() => {
    async function loadTasks() {
      setLoading(true);
      try {
        const plan = await getPlan(eventId);
        setTasks(plan.tasks || []);
      } catch {
        setTasks([]);
      } finally {
        setLoading(false);
      }
    }
    loadTasks();
  }, [eventId]);

  const filtered = tasks.filter((t) => {
    const matchSearch = t.name.toLowerCase().includes(search.toLowerCase());
    const matchStatus = statusFilter === "ALL" || t.status === statusFilter;
    return matchSearch && matchStatus;
  });

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-6">
      <div className="border-b border-slate-800 pb-5">
        <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-blue-950 text-blue-400 border border-blue-800 font-bold">
          OPERATIONAL TASKS
        </span>
        <h1 className="text-2xl md:text-3xl font-extrabold text-white mt-1">
          Task Inventory & Readiness
        </h1>
        <p className="text-xs text-slate-400 mt-0.5">
          All materialized tasks from the authoritative planning engine.
        </p>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
          <input
            type="text"
            placeholder="Search tasks..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-600"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-blue-600"
        >
          <option value="ALL">All Statuses</option>
          <option value="PENDING">PENDING</option>
          <option value="READY">READY</option>
          <option value="IN_PROGRESS">IN_PROGRESS</option>
          <option value="COMPLETED">COMPLETED</option>
          <option value="BLOCKED">BLOCKED</option>
        </select>
      </div>

      {/* Tasks List */}
      <div className="space-y-2.5">
        {filtered.map((t) => (
          <div
            key={t.id}
            className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs"
          >
            <div className="flex items-start space-x-3">
              <span
                className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase mt-0.5 ${
                  t.priority === "CRITICAL"
                    ? "bg-red-950 text-red-400 border border-red-800"
                    : "bg-slate-800 text-slate-300"
                }`}
              >
                {t.priority}
              </span>
              <div>
                <div className="flex items-center space-x-2">
                  <span className="font-bold text-white text-sm">{t.name}</span>
                  {t.is_critical_path && (
                    <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-red-950 text-red-300 border border-red-800 font-bold">
                      CRITICAL PATH
                    </span>
                  )}
                </div>
                <p className="text-slate-400 text-xs mt-0.5">{t.description || "Operational task"}</p>
              </div>
            </div>

            <div className="flex items-center space-x-4 font-mono text-[11px] text-slate-400 border-t md:border-t-0 pt-2 md:pt-0 border-slate-800">
              <div>
                <span className="text-slate-500">CATEGORY: </span>
                <span className="text-slate-300 uppercase">{t.required_provider_category || "GENERAL"}</span>
              </div>
              <div>
                <span className="text-slate-500">DURATION: </span>
                <span className="text-slate-300">{t.duration_minutes || 60}m</span>
              </div>
              <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 uppercase text-[10px]">
                {t.status}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
