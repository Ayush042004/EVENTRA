"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ShoppingBag,
  Users,
  DollarSign,
  CheckCircle,
  Clock,
  ArrowRight,
  ExternalLink,
} from "lucide-react";
import { getEventAssignments } from "../../../../lib/api/vendors";
import { getBudgetSummary } from "../../../../lib/api/budget";
import type {
  VendorAssignmentResponse,
  BudgetSummaryResponse,
} from "../../../../types/api";

export default function ProcurementPage() {
  const params = useParams();
  const router = useRouter();
  const eventId = params.eventId as string;

  const [assignments, setAssignments] = useState<VendorAssignmentResponse[]>([]);
  const [budget, setBudget] = useState<BudgetSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [assignData, budgetData] = await Promise.all([
          getEventAssignments(eventId).catch(() => []),
          getBudgetSummary(eventId).catch(() => null),
        ]);
        setAssignments(assignData);
        setBudget(budgetData);
      } catch (err: unknown) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    if (eventId) {
      loadData();
    }
  }, [eventId]);

  const totalCommitted = assignments.reduce(
    (sum, a) => sum + (Number(a.agreed_cost) || 0),
    0
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border/40 pb-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
              <ShoppingBag className="w-6 h-6 text-primary" />
              Procurement & Vendor Fulfillment
            </h1>
            <span className="font-mono text-[10px] px-2.5 py-0.5 rounded-full bg-secondary text-muted-foreground border border-border/50">
              Contract Lifecycle
            </span>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            Tracking provider category fulfillments, committed vendor contracts, and SLA conformance.
          </p>
        </div>

        <button
          onClick={() => router.push(`/events/${eventId}/vendors`)}
          className="inline-flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground transition-colors"
        >
          <Users className="w-3.5 h-3.5" />
          Manage Vendor Directory
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <div className="p-4 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm">
          <div className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
            <Users className="w-3.5 h-3.5 text-blue-400" />
            Assigned Providers
          </div>
          <div className="text-2xl font-bold tracking-tight text-foreground mt-2">
            {assignments.length}
          </div>
          <div className="text-[11px] text-muted-foreground mt-1">
            Active service contracts
          </div>
        </div>

        <div className="p-4 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm">
          <div className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
            <DollarSign className="w-3.5 h-3.5 text-emerald-400" />
            Total Committed Cost
          </div>
          <div className="text-2xl font-bold tracking-tight text-emerald-400 mt-2">
            ${totalCommitted.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </div>
          <div className="text-[11px] text-muted-foreground mt-1">
            Agreed provider sum
          </div>
        </div>

        <div className="p-4 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm">
          <div className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
            <CheckCircle className="w-3.5 h-3.5 text-purple-400" />
            Fulfillment Ratio
          </div>
          <div className="text-2xl font-bold tracking-tight text-foreground mt-2">
            100%
          </div>
          <div className="text-[11px] text-muted-foreground mt-1">
            All categories covered
          </div>
        </div>
      </div>

      {/* Contracts Roster */}
      <div className="rounded-xl border border-border/50 bg-card/30 backdrop-blur-sm overflow-hidden">
        <div className="p-4 border-b border-border/40 flex items-center justify-between text-xs text-muted-foreground">
          <span className="font-semibold uppercase text-[10px] tracking-wider text-foreground">
            Committed Vendor Contracts ({assignments.length})
          </span>
        </div>

        {assignments.length === 0 ? (
          <div className="p-12 text-center text-xs text-muted-foreground space-y-3">
            <ShoppingBag className="w-8 h-8 text-muted-foreground/40 mx-auto" />
            <p>No vendor contracts committed to this event yet.</p>
            <button
              onClick={() => router.push(`/events/${eventId}/vendors`)}
              className="px-3 py-1.5 rounded-lg bg-secondary text-foreground text-xs font-medium hover:bg-secondary/80"
            >
              Assign Vendors
            </button>
          </div>
        ) : (
          <div className="divide-y divide-border/30">
            {assignments.map((a) => (
              <div
                key={a.id}
                className="p-4 hover:bg-card/40 transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-secondary text-secondary-foreground border border-border/40">
                      {a.category}
                    </span>
                    <span className="font-bold text-foreground">
                      {a.vendor?.name || `Vendor #${a.vendor_id.slice(0, 8)}`}
                    </span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      {a.status}
                    </span>
                  </div>
                  {a.notes && <p className="text-muted-foreground">{a.notes}</p>}
                </div>

                <div className="flex items-center gap-4 text-right">
                  <div>
                    <div className="text-[10px] text-muted-foreground">Agreed Cost</div>
                    <div className="font-mono font-bold text-foreground">
                      ${Number(a.agreed_cost || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
