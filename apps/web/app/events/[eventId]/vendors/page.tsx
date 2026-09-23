"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { ProviderSearch } from "@/features/provider-network/ProviderSearch";
import { VendorResponse } from "@eventra/contracts";
import { Users, Calendar, MapPin, CheckCircle, ShieldAlert } from "lucide-react";

export default function EventVendorsPage() {
  const params = useParams();
  const eventId = params?.eventId as string;

  const [eventData, setEventData] = useState<any>(null);
  const [initialProviders, setInitialProviders] = useState<VendorResponse[]>([]);
  const [assignedVendorIds, setAssignedVendorIds] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [successBanner, setSuccessBanner] = useState<string | null>(null);

  const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

  useEffect(() => {
    if (!eventId) return;

    async function loadData() {
      try {
        setLoading(true);

        // Fetch event details
        const eventRes = await fetch(`${apiBase}/events/${eventId}`).catch(() => null);
        if (eventRes && eventRes.ok) {
          const ev = await eventRes.json();
          setEventData(ev);
        }

        // Fetch existing providers
        const vendorsRes = await fetch(`${apiBase}/vendors?limit=50`).catch(() => null);
        if (vendorsRes && vendorsRes.ok) {
          const vData = await vendorsRes.json();
          setInitialProviders(vData.items || []);
        }

        // Fetch event assignments
        const assignRes = await fetch(`${apiBase}/vendors/assignments/event/${eventId}`).catch(() => null);
        if (assignRes && assignRes.ok) {
          const aData = await assignRes.json();
          setAssignedVendorIds(aData.map((a: any) => a.vendor_id));
        }
      } catch (err) {
        console.error("Failed to load initial event vendor data:", err);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [eventId, apiBase]);

  const handleAssignProvider = async (provider: VendorResponse) => {
    try {
      const res = await fetch(`${apiBase}/vendors/assignments`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          event_id: eventId,
          vendor_id: provider.id,
          category: provider.category.toLowerCase(),
          status: "CONFIRMED",
          agreed_cost: provider.base_cost || 3000.0,
          notes: `Assigned via Google Maps discovery (${provider.name})`,
        }),
      });

      if (!res.ok) {
        throw new Error("Failed to record provider assignment.");
      }

      setAssignedVendorIds((prev) => [...prev, provider.id]);
      setSuccessBanner(`Successfully assigned "${provider.name}" (${provider.category}) to the event.`);
      setTimeout(() => setSuccessBanner(null), 5000);
    } catch (err: any) {
      alert(err.message || "Failed to assign provider.");
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 p-6 md:p-10 text-slate-100">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Page Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-6">
          <div>
            <div className="flex items-center gap-2.5">
              <span className="rounded-lg bg-cyan-950/80 px-2.5 py-1 text-xs font-mono font-semibold text-cyan-400 border border-cyan-800/60">
                PROVIDER NETWORK
              </span>
              {eventData?.event_type && (
                <span className="rounded-lg bg-slate-800 px-2.5 py-1 text-xs font-medium text-slate-300 border border-slate-700">
                  {eventData.event_type}
                </span>
              )}
            </div>
            <h1 className="text-2xl md:text-3xl font-black text-slate-100 tracking-tight mt-2">
              {eventData?.name || "Event Provider Network"}
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Search, discover, and assign real-world service providers and backup contractors.
            </p>
          </div>

          {/* Quick Context Pill */}
          {eventData && (
            <div className="flex flex-wrap items-center gap-4 bg-slate-900/80 border border-slate-800 px-4 py-3 rounded-xl text-xs text-slate-300">
              {eventData.guest_count > 0 && (
                <div className="flex items-center gap-1.5">
                  <Users className="h-4 w-4 text-cyan-400" />
                  <span>{eventData.guest_count} Guests</span>
                </div>
              )}
              {eventData.location && (
                <div className="flex items-center gap-1.5">
                  <MapPin className="h-4 w-4 text-emerald-400" />
                  <span>{eventData.location}</span>
                </div>
              )}
              <div className="flex items-center gap-1.5">
                <Calendar className="h-4 w-4 text-amber-400" />
                <span>{eventData.state || "ACTIVE"}</span>
              </div>
            </div>
          )}
        </div>

        {/* Assignment Success Notification */}
        {successBanner && (
          <div className="rounded-xl border border-emerald-900/80 bg-emerald-950/60 p-4 text-sm text-emerald-300 flex items-center gap-3 animate-fadeIn">
            <CheckCircle className="h-5 w-5 text-emerald-400 shrink-0" />
            <span>{successBanner}</span>
          </div>
        )}

        {/* Main Provider Search & Discovery Component */}
        <ProviderSearch
          eventId={eventId}
          initialProviders={initialProviders}
          assignedVendorIds={assignedVendorIds}
          defaultCity={eventData?.location || "Noida"}
          onAssignProvider={handleAssignProvider}
        />
      </div>
    </div>
  );
}
