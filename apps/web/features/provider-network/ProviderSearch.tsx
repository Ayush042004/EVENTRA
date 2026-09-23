"use client";

import React, { useState } from "react";
import { VendorResponse, ProviderDiscoveryResponse } from "@eventra/contracts";
import { ProviderCard } from "./ProviderCard";
import { Search, MapPin, Sparkles, Filter, RefreshCw, AlertCircle, CheckCircle } from "lucide-react";

const CONTROLLED_CATEGORIES = [
  { value: "CATERING", label: "Catering" },
  { value: "VENUE", label: "Venue" },
  { value: "DECOR", label: "Decor & Styling" },
  { value: "PHOTOGRAPHY", label: "Photography" },
  { value: "VIDEOGRAPHY", label: "Videography & Film" },
  { value: "DJ_MUSIC", label: "DJ & Music" },
  { value: "LIGHTING", label: "Lighting" },
  { value: "AV_TECH", label: "AV & Sound Equipment" },
  { value: "ENTERTAINMENT", label: "Live Entertainment" },
  { value: "TRANSPORT", label: "Transport & Logistics" },
  { value: "SECURITY", label: "Security & Bouncers" },
  { value: "STAFFING", label: "Hospitality Staffing" },
  { value: "MAKEUP_STYLING", label: "Makeup & Styling" },
  { value: "PRINTING", label: "Printing & Invites" },
  { value: "RENTALS", label: "Rentals & Furniture" },
  { value: "FLORIST", label: "Florist & Flowers" },
  { value: "PRODUCTION", label: "Stage Production" },
  { value: "CLEANING", label: "Cleaning & Sanitation" },
  { value: "OTHER", label: "Other Services" },
];

interface ProviderSearchProps {
  eventId?: string;
  initialProviders?: VendorResponse[];
  assignedVendorIds?: string[];
  defaultCity?: string;
  onAssignProvider?: (provider: VendorResponse) => Promise<void> | void;
}

export function ProviderSearch({
  eventId,
  initialProviders = [],
  assignedVendorIds = [],
  defaultCity = "Noida",
  onAssignProvider,
}: ProviderSearchProps) {
  const [providers, setProviders] = useState<VendorResponse[]>(initialProviders);
  const [category, setCategory] = useState<string>("CATERING");
  const [location, setLocation] = useState<string>(defaultCity);
  const [query, setQuery] = useState<string>("wedding caterers");
  const [isDiscovering, setIsDiscovering] = useState<boolean>(false);
  const [discoveryMeta, setDiscoveryMeta] = useState<ProviderDiscoveryResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [activeFilterCategory, setActiveFilterCategory] = useState<string>("ALL");
  const [assigningId, setAssigningId] = useState<string | null>(null);

  const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

  const handleDiscover = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setIsDiscovering(true);
    setErrorMsg(null);

    const endpoint = eventId
      ? `${apiBase}/events/${eventId}/providers/discover`
      : `${apiBase}/vendors/discover`;

    try {
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          category,
          location: location.trim(),
          query: query.trim(),
          limit: 15,
        }),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.message || `Discovery failed with status ${res.status}`);
      }

      const data: ProviderDiscoveryResponse = await res.json();
      setDiscoveryMeta(data);

      // Merge newly discovered items into local list without duplicates
      setProviders((prev) => {
        const existingMap = new Map(prev.map((p) => [p.id, p]));
        for (const item of data.items) {
          existingMap.set(item.id, item);
        }
        return Array.from(existingMap.values());
      });
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to reach Google Maps discovery engine.");
    } finally {
      setIsDiscovering(false);
    }
  };

  const handleAssign = async (provider: VendorResponse) => {
    if (!onAssignProvider) return;
    setAssigningId(provider.id);
    try {
      await onAssignProvider(provider);
    } finally {
      setAssigningId(null);
    }
  };

  const filteredProviders = providers.filter((p) => {
    if (activeFilterCategory !== "ALL" && p.category.toUpperCase() !== activeFilterCategory) {
      return false;
    }
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Discovery Control Panel */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-5 shadow-xl backdrop-blur-md">
        <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-800">
          <div>
            <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-cyan-400" />
              Discover Providers via Google Maps
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Live external business discovery, structured normalization, and controlled taxonomy classification.
            </p>
          </div>
          <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-800 px-3 py-1 text-xs font-mono text-cyan-400 border border-slate-700">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            19 Taxonomy Categories
          </span>
        </div>

        <form onSubmit={handleDiscover} className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-12">
          {/* Category Dropdown */}
          <div className="sm:col-span-3">
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
              Provider Category
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full rounded-xl border border-slate-700 bg-slate-800/90 px-3 py-2.5 text-sm text-slate-100 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500"
            >
              {CONTROLLED_CATEGORIES.map((cat) => (
                <option key={cat.value} value={cat.value} className="bg-slate-900 text-slate-100">
                  {cat.label}
                </option>
              ))}
            </select>
          </div>

          {/* Location Input */}
          <div className="sm:col-span-3">
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
              Location / City
            </label>
            <div className="relative">
              <MapPin className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="e.g. Noida or Delhi NCR"
                className="w-full rounded-xl border border-slate-700 bg-slate-800/90 pl-9 pr-3 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500"
              />
            </div>
          </div>

          {/* Query / Requirement Input */}
          <div className="sm:col-span-4">
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
              Search Query / Requirement
            </label>
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g. wedding caterers for 500 guests"
                className="w-full rounded-xl border border-slate-700 bg-slate-800/90 pl-9 pr-3 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500"
              />
            </div>
          </div>

          {/* Submit Action */}
          <div className="sm:col-span-2 flex items-end">
            <button
              type="submit"
              disabled={isDiscovering}
              className="w-full inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 px-4 py-2.5 text-sm font-bold text-white shadow-lg hover:from-cyan-500 hover:to-blue-500 disabled:opacity-50 transition-all duration-200 active:scale-98"
            >
              <RefreshCw className={`h-4 w-4 ${isDiscovering ? "animate-spin" : ""}`} />
              {isDiscovering ? "Searching…" : "Discover"}
            </button>
          </div>
        </form>

        {/* Discovery Summary Feedback Banner */}
        {discoveryMeta && (
          <div className="mt-4 rounded-xl border border-emerald-900/60 bg-emerald-950/40 p-3.5 text-xs text-emerald-300 flex items-start justify-between gap-3 animate-fadeIn">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-emerald-400 shrink-0" />
              <div>
                <span className="font-semibold text-emerald-200">
                  Discovered {discoveryMeta.total_discovered} real-world businesses
                </span>{" "}
                ({discoveryMeta.total_created} new, {discoveryMeta.total_updated} enriched).
                <div className="text-[11px] text-emerald-400/80 mt-0.5">
                  Source: <span className="font-mono">{discoveryMeta.source}</span> • Classified into controlled EVENTRA taxonomy.
                </div>
              </div>
            </div>
            {discoveryMeta.query_used && discoveryMeta.query_used.length > 0 && (
              <span className="text-[11px] text-slate-400 hidden md:inline-block font-mono">
                Query: "{discoveryMeta.query_used[0]}"
              </span>
            )}
          </div>
        )}

        {/* Error Notification */}
        {errorMsg && (
          <div className="mt-4 rounded-xl border border-rose-900/60 bg-rose-950/40 p-3.5 text-xs text-rose-300 flex items-center gap-2.5">
            <AlertCircle className="h-4 w-4 text-rose-400 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}
      </div>

      {/* Filter Tabs & Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-slate-400" />
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Filter Providers:
          </span>
          <div className="flex flex-wrap gap-1.5">
            {["ALL", "CATERING", "DECOR", "PHOTOGRAPHY", "DJ_MUSIC", "AV_TECH", "VENUE"].map((cat) => (
              <button
                key={cat}
                onClick={() => setActiveFilterCategory(cat)}
                className={`rounded-lg px-2.5 py-1 text-xs font-medium transition-colors ${
                  activeFilterCategory === cat
                    ? "bg-cyan-500 text-slate-950 font-semibold"
                    : "bg-slate-900 text-slate-400 hover:bg-slate-800 hover:text-slate-200"
                }`}
              >
                {cat === "ALL" ? "All Categories" : cat.replace(/_/g, " ")}
              </button>
            ))}
          </div>
        </div>

        <span className="text-xs text-slate-400">
          Showing <strong className="text-slate-200">{filteredProviders.length}</strong> providers
        </span>
      </div>

      {/* Provider Card Grid */}
      {filteredProviders.length > 0 ? (
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {filteredProviders.map((prov) => (
            <ProviderCard
              key={prov.id}
              provider={prov}
              isAssigned={assignedVendorIds.includes(prov.id)}
              onAssign={onAssignProvider ? handleAssign : undefined}
              assigning={assigningId === prov.id}
            />
          ))}
        </div>
      ) : (
        <div className="rounded-2xl border border-dashed border-slate-800 bg-slate-900/40 p-12 text-center">
          <Search className="mx-auto h-8 w-8 text-slate-600" />
          <h3 className="mt-3 text-sm font-semibold text-slate-300">No Providers in this View</h3>
          <p className="mt-1 text-xs text-slate-500 max-w-sm mx-auto">
            Use the discovery bar above to search Google Maps for real catering, decor, audiovisual, or entertainment providers.
          </p>
        </div>
      )}
    </div>
  );
}
