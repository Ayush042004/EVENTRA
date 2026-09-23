"use client";

import React, { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import {
  DollarSign,
  TrendingDown,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  ShieldCheck,
  RefreshCw,
  PieChart,
  List,
} from "lucide-react";
import { getBudgetSummary, validateBudget } from "../../../../lib/api/budget";
import type {
  BudgetSummaryResponse,
  BudgetValidationResponse,
} from "../../../../types/api";

export default function BudgetPage() {
  const params = useParams();
  const eventId = params.eventId as string;

  const [summary, setSummary] = useState<BudgetSummaryResponse | null>(null);
  const [validation, setValidation] = useState<BudgetValidationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [validating, setValidating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadData() {
    try {
      setLoading(true);
      setError(null);
      const [sumData, valData] = await Promise.all([
        getBudgetSummary(eventId),
        validateBudget(eventId),
      ]);
      setSummary(sumData);
      setValidation(valData);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load budget data";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  async function handleValidate() {
    try {
      setValidating(true);
      const valData = await validateBudget(eventId);
      setValidation(valData);
    } catch (err: unknown) {
      console.error("Validation error:", err);
    } finally {
      setValidating(false);
    }
  }

  useEffect(() => {
    if (eventId) {
      loadData();
    }
  }, [eventId]);

  const totalBudget = summary?.total_budget || 0;
  const totalEstimated = summary?.total_estimated || 0;
  const totalActual = summary?.total_actual || 0;
  const remaining = summary?.remaining || 0;
  const items = summary?.items || [];
  const categories = summary?.categories || {};

  const budgetUtilization = totalBudget > 0 ? (totalActual / totalBudget) * 100 : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border/40 pb-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              Budget & Financial Guardrails
            </h1>
            {validation && (
              <span
                className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                  validation.is_valid
                    ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                    : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                }`}
              >
                {validation.is_valid ? (
                  <CheckCircle className="w-3.5 h-3.5" />
                ) : (
                  <AlertTriangle className="w-3.5 h-3.5" />
                )}
                {validation.is_valid ? "CEILING COMPLIANT" : "BUDGET OVERRUN"}
              </span>
            )}
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            Real-time financial variance calculation, category allocation caps, and commitment auditing.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={loadData}
            disabled={loading}
            className="inline-flex items-center gap-2 px-3 py-1.5 text-xs font-medium rounded-lg border border-border/60 hover:bg-card/60 text-muted-foreground hover:text-foreground transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
          <button
            onClick={handleValidate}
            disabled={validating}
            className="inline-flex items-center gap-2 px-4 py-1.5 text-xs font-semibold rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground shadow-sm transition-colors"
          >
            <ShieldCheck className={`w-3.5 h-3.5 ${validating ? "animate-spin" : ""}`} />
            {validating ? "Validating Guardrails..." : "Validate Guardrails"}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl border border-rose-500/30 bg-rose-500/5 text-rose-300 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Violations Banner */}
      {validation && !validation.is_valid && validation.violations.length > 0 && (
        <div className="p-4 rounded-xl border border-rose-500/30 bg-rose-500/5 space-y-2">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-400" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-rose-300">
              Active Budget Violations Detected ({validation.violations.length})
            </h3>
          </div>
          <div className="grid gap-2">
            {validation.violations.map((v, i) => (
              <div
                key={i}
                className="p-3 rounded-lg bg-background/60 border border-rose-500/20 flex items-center justify-between text-xs"
              >
                <div>
                  <span className="font-semibold text-rose-300 uppercase mr-2">
                    {v.category || "GENERAL"} [{v.violation_type}]
                  </span>
                  <span className="text-muted-foreground">{v.description}</span>
                </div>
                <div className="font-mono font-bold text-rose-400">
                  +${v.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Financial KPI Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm">
          <div className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
            <DollarSign className="w-3.5 h-3.5 text-blue-400" />
            Total Budget Ceiling
          </div>
          <div className="text-2xl font-bold tracking-tight text-foreground mt-2">
            ${totalBudget.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </div>
          <div className="text-[11px] text-muted-foreground mt-1">
            Authoritative event cap
          </div>
        </div>

        <div className="p-4 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm">
          <div className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
            <TrendingUp className="w-3.5 h-3.5 text-amber-400" />
            Total Estimated
          </div>
          <div className="text-2xl font-bold tracking-tight text-amber-400 mt-2">
            ${totalEstimated.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </div>
          <div className="text-[11px] text-muted-foreground mt-1">
            {summary?.item_count ?? 0} planned items
          </div>
        </div>

        <div className="p-4 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm">
          <div className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
            <TrendingDown className="w-3.5 h-3.5 text-rose-400" />
            Committed / Actual
          </div>
          <div className="text-2xl font-bold tracking-tight text-foreground mt-2">
            ${totalActual.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </div>
          <div className="text-[11px] text-muted-foreground mt-1">
            {budgetUtilization.toFixed(1)}% utilized
          </div>
        </div>

        <div className="p-4 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm">
          <div className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
            <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
            Remaining Slack
          </div>
          <div
            className={`text-2xl font-bold tracking-tight mt-2 ${
              remaining >= 0 ? "text-emerald-400" : "text-rose-400"
            }`}
          >
            ${remaining.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </div>
          <div className="text-[11px] text-muted-foreground mt-1">
            {remaining >= 0 ? "Uncommitted reserve" : "Deficit exceeded"}
          </div>
        </div>
      </div>

      {/* Category Breakdown & Allocation Bar */}
      <div className="p-5 rounded-xl border border-border/50 bg-card/30 backdrop-blur-sm space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <PieChart className="w-4 h-4 text-blue-400" />
            <h2 className="text-sm font-semibold text-foreground">
              Category Allocation Breakdown
            </h2>
          </div>
          <span className="text-xs text-muted-foreground">
            {Object.keys(categories).length} Active Categories
          </span>
        </div>

        {/* Global Progress Bar */}
        <div className="space-y-1">
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>Utilization vs Cap</span>
            <span>{budgetUtilization.toFixed(1)}%</span>
          </div>
          <div className="w-full bg-secondary/40 h-2.5 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${
                budgetUtilization > 100
                  ? "bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.6)]"
                  : budgetUtilization > 85
                  ? "bg-amber-500"
                  : "bg-emerald-500"
              }`}
              style={{ width: `${Math.min(budgetUtilization, 100)}%` }}
            />
          </div>
        </div>

        {/* Category Pills / Metrics */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 pt-2">
          {Object.entries(categories).map(([cat, amount]) => {
            const catPercent = totalEstimated > 0 ? (amount / totalEstimated) * 100 : 0;
            return (
              <div
                key={cat}
                className="p-3 rounded-lg border border-border/40 bg-card/50 flex flex-col justify-between"
              >
                <div className="text-[10px] font-semibold tracking-wider text-muted-foreground uppercase truncate">
                  {cat.replace("_", " ")}
                </div>
                <div className="flex items-baseline justify-between mt-2">
                  <span className="text-sm font-bold text-foreground">
                    ${amount.toLocaleString(undefined, { minimumFractionDigits: 0 })}
                  </span>
                  <span className="text-[10px] text-muted-foreground">
                    {catPercent.toFixed(0)}%
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Materialized Budget Items List */}
      <div className="rounded-xl border border-border/50 bg-card/30 backdrop-blur-sm overflow-hidden">
        <div className="p-4 border-b border-border/40 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <List className="w-4 h-4 text-primary" />
            <h2 className="text-sm font-semibold text-foreground">
              Materialized Line-Item Budget
            </h2>
          </div>
          <span className="text-xs text-muted-foreground">
            {items.length} Line Items
          </span>
        </div>

        {items.length === 0 ? (
          <div className="p-8 text-center text-xs text-muted-foreground">
            No budget items materialized for this event yet.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-secondary/20 text-muted-foreground uppercase tracking-wider text-[10px] border-b border-border/30">
                <tr>
                  <th className="py-3 px-4">Line Item</th>
                  <th className="py-3 px-4">Category</th>
                  <th className="py-3 px-4 text-right">Estimated</th>
                  <th className="py-3 px-4 text-right">Actual / Committed</th>
                  <th className="py-3 px-4 text-right">Variance</th>
                  <th className="py-3 px-4 text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/30">
                {items.map((item) => {
                  const est = Number(item.estimated_amount) || 0;
                  const act = Number(item.actual_amount) || 0;
                  const variance = act - est;

                  return (
                    <tr key={item.id} className="hover:bg-card/40 transition-colors">
                      <td className="py-3 px-4 font-medium text-foreground">
                        {item.name}
                      </td>
                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-secondary text-secondary-foreground border border-border/40">
                          {item.category}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right font-mono text-muted-foreground">
                        ${est.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </td>
                      <td className="py-3 px-4 text-right font-mono font-semibold text-foreground">
                        ${act.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </td>
                      <td
                        className={`py-3 px-4 text-right font-mono font-medium ${
                          variance > 0
                            ? "text-rose-400"
                            : variance < 0
                            ? "text-emerald-400"
                            : "text-muted-foreground"
                        }`}
                      >
                        {variance > 0 ? `+` : ""}
                        ${variance.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span
                          className={`inline-flex px-2 py-0.5 rounded text-[10px] font-bold ${
                            item.status === "PAID"
                              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                              : item.status === "COMMITTED"
                              ? "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                              : "bg-secondary text-muted-foreground border border-border/40"
                          }`}
                        >
                          {item.status}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
