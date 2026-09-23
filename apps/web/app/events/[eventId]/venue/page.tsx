"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { searchVenues, checkVenueAvailability, checkVenueSuitability } from "../../../../lib/api/venues";
import { useEvent } from "../../../../hooks/useEvent";
import type { VenueResponse, VenueAvailabilityResult, VenueSuitabilityResult } from "../../../../types/api";
import {
  Building2,
  Search,
  Filter,
  Users,
  DollarSign,
  MapPin,
  CheckCircle2,
  XCircle,
  Clock,
  Sparkles,
  ChevronRight,
} from "lucide-react";

export default function VenueDiscoveryPage() {
  const params = useParams();
  const eventId = params?.eventId as string;

  const { event, specification } = useEvent(eventId);

  const [venues, setVenues] = useState<VenueResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [cityFilter, setCityFilter] = useState("");
  const [minCapacity, setMinCapacity] = useState<number | undefined>(undefined);
  const [selectedVenue, setSelectedVenue] = useState<VenueResponse | null>(null);

  const [availResult, setAvailResult] = useState<VenueAvailabilityResult | null>(null);
  const [checkingAvail, setCheckingAvail] = useState(false);

  const [suitResult, setSuitResult] = useState<VenueSuitabilityResult | null>(null);
  const [evaluatingSuit, setEvaluatingSuit] = useState(false);

  const fetchVenues = async () => {
    setLoading(true);
    try {
      const res = await searchVenues({
        city: cityFilter || undefined,
        min_capacity: minCapacity || undefined,
      });
      setVenues(res.items || []);
      if (res.items?.length > 0 && !selectedVenue) {
        setSelectedVenue(res.items[0]);
      }
    } catch (err) {
      console.error("Venue search error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVenues();
  }, [cityFilter, minCapacity]);

  const handleCheckAvailability = async (venueId: string) => {
    setCheckingAvail(true);
    setAvailResult(null);
    try {
      const start = event?.start_datetime || new Date().toISOString();
      const end = event?.end_datetime || new Date(Date.now() + 3600 * 1000 * 8).toISOString();
      const res = await checkVenueAvailability(venueId, start, end);
      setAvailResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setCheckingAvail(false);
    }
  };

  const handleCheckSuitability = async (venueId: string) => {
    setEvaluatingSuit(true);
    setSuitResult(null);
    try {
      const guestCount = event?.guest_count || specification?.guest_count || 200;
      const res = await checkVenueSuitability(venueId, {
        guest_count: guestCount,
        max_hourly_rate: 1000,
      });
      setSuitResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setEvaluatingSuit(false);
    }
  };

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-blue-950 text-blue-400 border border-blue-800 font-bold">
            FACILITIES DISCOVERY
          </span>
          <h1 className="text-2xl md:text-3xl font-extrabold text-white mt-1">
            Venue Network & Physical Suitability
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Deterministic search, real-time availability window checks, and capacity suitability scorecard.
          </p>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 flex flex-wrap items-center gap-3">
        <div className="flex items-center space-x-2">
          <Filter className="w-4 h-4 text-slate-500" />
          <span className="text-xs font-bold text-slate-300 uppercase">Filters:</span>
        </div>
        <input
          type="text"
          placeholder="Filter by city (e.g. San Francisco)..."
          value={cityFilter}
          onChange={(e) => setCityFilter(e.target.value)}
          className="px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-600"
        />
        <input
          type="number"
          placeholder="Min capacity (e.g. 150)..."
          value={minCapacity || ""}
          onChange={(e) => setMinCapacity(e.target.value ? Number(e.target.value) : undefined)}
          className="px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 w-44 focus:outline-none focus:border-blue-600"
        />
      </div>

      {/* Content Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Venues List */}
        <div className="lg:col-span-2 space-y-3">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
            Available Venues ({venues.length})
          </h3>

          {loading ? (
            <div className="py-16 text-center text-xs text-slate-500 font-mono">
              Querying Venue Network...
            </div>
          ) : (
            <div className="space-y-3">
              {venues.map((v) => {
                const isSelected = selectedVenue?.id === v.id;
                return (
                  <div
                    key={v.id}
                    onClick={() => {
                      setSelectedVenue(v);
                      setAvailResult(null);
                      setSuitResult(null);
                    }}
                    className={`p-5 rounded-xl border cursor-pointer transition flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${
                      isSelected
                        ? "bg-slate-900 border-blue-500/80 shadow-lg shadow-blue-950/40"
                        : "bg-slate-900/50 border-slate-800 hover:border-slate-700"
                    }`}
                  >
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 uppercase">
                          {v.venue_type}
                        </span>
                        <span className="text-[10px] font-mono text-emerald-400 font-semibold">
                          {v.status}
                        </span>
                      </div>
                      <h4 className="text-base font-bold text-white mt-1">{v.name}</h4>
                      <p className="text-xs text-slate-400 flex items-center space-x-1 mt-1">
                        <MapPin className="w-3.5 h-3.5 text-slate-500" />
                        <span>{v.address ? `${v.address}, ` : ""}{v.city}</span>
                      </p>

                      <div className="flex flex-wrap gap-1.5 mt-3">
                        {v.amenities?.slice(0, 4).map((a, idx) => (
                          <span
                            key={idx}
                            className="text-[10px] px-2 py-0.5 rounded bg-slate-950 border border-slate-850 text-slate-400"
                          >
                            {a}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="text-right flex sm:flex-col justify-between sm:justify-center items-end border-t sm:border-t-0 pt-2 sm:pt-0 border-slate-800 text-xs font-mono">
                      <div>
                        <div className="text-[10px] text-slate-500">MAX CAPACITY</div>
                        <div className="font-bold text-slate-200">{v.capacity} guests</div>
                      </div>
                      <div className="sm:mt-2">
                        <div className="text-[10px] text-slate-500">RATE</div>
                        <div className="font-bold text-emerald-400">${v.hourly_rate || 0}/hr</div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Selected Venue Inspection & Suitability Scorecard */}
        <div className="space-y-4">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
            Operational Inspection
          </h3>

          {selectedVenue ? (
            <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/60 space-y-4">
              <div>
                <span className="text-[10px] font-mono text-slate-500 uppercase">INSPECTING VENUE</span>
                <h3 className="text-lg font-bold text-white">{selectedVenue.name}</h3>
                <p className="text-xs text-slate-400 mt-0.5">{selectedVenue.city}</p>
              </div>

              {/* Action Buttons: Availability & Suitability */}
              <div className="space-y-2 pt-2 border-t border-slate-800">
                <button
                  onClick={() => handleCheckAvailability(selectedVenue.id)}
                  disabled={checkingAvail}
                  className="w-full py-2 px-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center justify-center space-x-2 border border-slate-700 transition"
                >
                  <Clock className="w-3.5 h-3.5 text-blue-400" />
                  <span>{checkingAvail ? "Checking..." : "Check Availability Window"}</span>
                </button>

                <button
                  onClick={() => handleCheckSuitability(selectedVenue.id)}
                  disabled={evaluatingSuit}
                  className="w-full py-2 px-3 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold flex items-center justify-center space-x-2 shadow-md transition"
                >
                  <Sparkles className="w-3.5 h-3.5 text-white" />
                  <span>{evaluatingSuit ? "Evaluating..." : "Evaluate Suitability Scorecard"}</span>
                </button>
              </div>

              {/* Availability Result */}
              {availResult && (
                <div className={`p-3 rounded-lg border text-xs font-mono ${
                  availResult.is_available
                    ? "bg-emerald-950/40 border-emerald-600/50 text-emerald-300"
                    : "bg-red-950/40 border-red-600/50 text-red-300"
                }`}>
                  <div className="font-bold flex items-center space-x-1.5">
                    {availResult.is_available ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    ) : (
                      <XCircle className="w-4 h-4 text-red-400" />
                    )}
                    <span>{availResult.is_available ? "VENUE AVAILABLE" : "VENUE OCCUPIED / BLOCKED"}</span>
                  </div>
                  <div className="text-[11px] mt-1 text-slate-300">
                    Checked window: {event?.start_datetime ? new Date(event.start_datetime).toLocaleDateString() : "Active Timeline"}
                  </div>
                </div>
              )}

              {/* Suitability Result */}
              {suitResult && (
                <div className="p-3.5 rounded-lg bg-slate-950 border border-slate-800 space-y-2 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-200">Suitability Evaluation</span>
                    <span className={`font-mono px-2 py-0.5 rounded text-[10px] font-bold ${
                      suitResult.is_suitable
                        ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                        : "bg-red-950 text-red-300 border border-red-800"
                    }`}>
                      SCORE: {(suitResult.score * 100).toFixed(0)}%
                    </span>
                  </div>

                  <div className="space-y-1 font-mono text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Capacity Match:</span>
                      <span className={suitResult.capacity_match ? "text-emerald-400" : "text-red-400"}>
                        {suitResult.capacity_match ? "MATCH" : "INSUFFICIENT"}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Amenity Match:</span>
                      <span className={suitResult.amenity_match ? "text-emerald-400" : "text-amber-400"}>
                        {suitResult.amenity_match ? "COMPLIANT" : "PARTIAL"}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Budget Ceiling:</span>
                      <span className={suitResult.budget_match ? "text-emerald-400" : "text-red-400"}>
                        {suitResult.budget_match ? "WITHIN LIMIT" : "OVER BUDGET"}
                      </span>
                    </div>
                  </div>

                  {suitResult.reasons?.length > 0 && (
                    <div className="pt-2 border-t border-slate-850">
                      <span className="text-[10px] text-slate-500 font-mono">REASONS:</span>
                      <ul className="list-disc pl-4 text-[11px] text-slate-300 space-y-0.5 mt-0.5">
                        {suitResult.reasons.map((r, idx) => (
                          <li key={idx}>{r}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="p-8 rounded-xl border border-slate-800 bg-slate-900/40 text-center text-xs text-slate-500">
              Select a venue from the list to inspect operational details.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
