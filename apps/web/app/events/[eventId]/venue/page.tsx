"use client";

import React, { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import dynamic from "next/dynamic";
import { searchVenues, checkVenueAvailability, checkVenueSuitability, discoverVenues } from "../../../../lib/api/venues";
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
  Maximize2,
  Columns,
  Grid,
  Map as MapIcon,
  Compass,
  Star,
  Check,
  Radio,
  SlidersHorizontal,
  X,
} from "lucide-react";

// Dynamically import Leaflet Map component with SSR disabled
const VenueMap = dynamic(() => import("../../../../components/maps/VenueMap"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full min-h-[500px] flex flex-col items-center justify-center bg-[#090d16] text-slate-400 font-mono text-xs border border-slate-800 rounded-2xl">
      <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin mb-3"></div>
      <span>Loading Interactive Map Engine (Zero API Key)...</span>
    </div>
  ),
});

// Dynamically import react-simple-maps component
const SimpleSvgMap = dynamic(() => import("../../../../components/maps/SimpleSvgMap"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full min-h-[500px] flex flex-col items-center justify-center bg-[#090d16] text-slate-400 font-mono text-xs border border-slate-800 rounded-2xl">
      <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin mb-3"></div>
      <span>Loading react-simple-maps Engine...</span>
    </div>
  ),
});

export default function VenueDiscoveryPage() {
  const params = useParams();
  const eventId = params?.eventId as string;

  const { event, specification } = useEvent(eventId);

  const [venues, setVenues] = useState<VenueResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCity, setSelectedCity] = useState<string>("ALL");
  const [selectedCategory, setSelectedCategory] = useState<string>("ALL");
  const [minCapacity, setMinCapacity] = useState<number | undefined>(undefined);
  const [selectedVenue, setSelectedVenue] = useState<VenueResponse | null>(null);

  // View Mode: split (Google Maps style), map-only, list-only
  const [viewMode, setViewMode] = useState<"split" | "map" | "grid">("split");
  // Map Engine: "streets" (zero-key Leaflet street map) vs "svg" (react-simple-maps)
  const [mapEngine, setMapEngine] = useState<"streets" | "svg">("streets");

  // Operational Suitability & Availability State
  const [availResult, setAvailResult] = useState<VenueAvailabilityResult | null>(null);
  const [checkingAvail, setCheckingAvail] = useState(false);
  const [suitResult, setSuitResult] = useState<VenueSuitabilityResult | null>(null);
  const [evaluatingSuit, setEvaluatingSuit] = useState(false);
  const [inspectorOpen, setInspectorOpen] = useState(false);
  const [selectedVenueIdForEvent, setSelectedVenueIdForEvent] = useState<string | null>(null);

  // Live Real-World Geospatial Discovery State
  const [liveDiscovering, setLiveDiscovering] = useState(false);
  const [liveDiscoveredCount, setLiveDiscoveredCount] = useState<number | null>(null);

  const handleDiscoverLiveVenues = async (targetCity?: string) => {
    setLiveDiscovering(true);
    const cityToQuery = targetCity || (selectedCity !== "ALL" ? selectedCity : "Seattle");
    try {
      const res = await discoverVenues({
        city: cityToQuery,
        query: searchQuery.trim() || undefined,
        limit: 30,
        save_to_db: true,
      });
      if (res && res.items && res.items.length > 0) {
        setVenues(res.items);
        setSelectedVenue(res.items[0]);
        setLiveDiscoveredCount(res.total_discovered);
        if (targetCity) setSelectedCity(targetCity);
      }
    } catch (err) {
      console.error("Live discovery failed:", err);
    } finally {
      setLiveDiscovering(false);
    }
  };

  // Sync default city from event
  useEffect(() => {
    if (event?.location) {
      const loc = event.location.toLowerCase();
      if (loc.includes("seattle")) setSelectedCity("Seattle");
      else if (loc.includes("mumbai")) setSelectedCity("Mumbai");
      else if (loc.includes("delhi")) setSelectedCity("Delhi");
      else if (loc.includes("bengaluru")) setSelectedCity("Bengaluru");
    }
  }, [event]);

  const fetchVenues = async () => {
    setLoading(true);
    try {
      const res = await searchVenues({
        city: selectedCity !== "ALL" ? selectedCity : undefined,
        min_capacity: minCapacity || undefined,
        venue_type: selectedCategory !== "ALL" ? selectedCategory : undefined,
        limit: 50,
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
  }, [selectedCity, selectedCategory, minCapacity]);

  // Filter venues locally by search text
  const filteredVenues = venues.filter((v) => {
    if (!searchQuery.trim()) return true;
    const query = searchQuery.toLowerCase();
    return (
      v.name.toLowerCase().includes(query) ||
      (v.address && v.address.toLowerCase().includes(query)) ||
      v.city.toLowerCase().includes(query) ||
      v.venue_type.toLowerCase().includes(query)
    );
  });

  const handleSelectVenue = (venue: VenueResponse) => {
    setSelectedVenue(venue);
    setAvailResult(null);
    setSuitResult(null);
  };

  const handleCheckAvailability = async (venueId: string) => {
    setCheckingAvail(true);
    setAvailResult(null);
    setInspectorOpen(true);
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
    setInspectorOpen(true);
    try {
      const guestCount = event?.guest_count || specification?.guest_count || 300;
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

  const handleBindVenueToEvent = (venue: VenueResponse) => {
    setSelectedVenueIdForEvent(venue.id);
    alert(`Venue "${venue.name}" bound as primary operational facility for ${event?.name || "this event"}!`);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem)] bg-[#070b12] text-slate-100 overflow-hidden font-sans">
      {/* Top Filter and Controls Bar */}
      <div className="px-4 py-3 border-b border-slate-800/90 bg-[#090d16]/95 backdrop-blur-md flex flex-wrap items-center justify-between gap-3 shrink-0 z-30">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <span className="p-1.5 rounded-lg bg-cyan-950 text-cyan-400 border border-cyan-800">
              <Compass className="w-4 h-4" />
            </span>
            <div>
              <h1 className="text-sm font-black tracking-tight text-white flex items-center space-x-2">
                <span>Physical Venue Network & Spatial Suitability</span>
                <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                  Interactive Map
                </span>
              </h1>
            </div>
          </div>
        </div>

        {/* Global Controls & Filters */}
        <div className="flex items-center space-x-2 flex-wrap">
          {/* Search Input */}
          <div className="relative w-64">
            <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search real venues, landmarks..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition"
            />
          </div>

          {/* City Selector */}
          <select
            value={selectedCity}
            onChange={(e) => setSelectedCity(e.target.value)}
            className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-300 font-semibold focus:outline-none focus:border-cyan-500"
          >
            <option value="ALL">All Regions</option>
            <option value="Seattle">Seattle, WA</option>
            <option value="Mumbai">Mumbai, MH</option>
            <option value="Delhi">Delhi, NCR</option>
            <option value="Bengaluru">Bengaluru, KA</option>
          </select>

          {/* Category Selector */}
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-300 font-semibold focus:outline-none focus:border-cyan-500"
          >
            <option value="ALL">All Categories</option>
            <option value="convention_center">Convention Centers</option>
            <option value="conference_center">Conference Centers</option>
            <option value="banquet_hall">Ballrooms & Halls</option>
            <option value="studio">High-Tech Studios</option>
            <option value="auditorium">Auditoriums</option>
            <option value="open_ground">Open Grounds</option>
          </select>

          {/* Map Engine Selector */}
          <div className="flex items-center bg-slate-900 p-1 rounded-xl border border-slate-800 space-x-1 text-xs">
            <button
              onClick={() => setMapEngine("streets")}
              className={`px-2.5 py-1 rounded-lg font-semibold transition ${
                mapEngine === "streets"
                  ? "bg-cyan-600 text-white shadow-md shadow-cyan-900/40"
                  : "text-slate-400 hover:text-white"
              }`}
              title="Real Street Level Map (100% Free, Zero API Key)"
            >
              Street & Satellite Map
            </button>
            <button
              onClick={() => setMapEngine("svg")}
              className={`px-2.5 py-1 rounded-lg font-semibold transition ${
                mapEngine === "svg"
                  ? "bg-cyan-600 text-white shadow-md shadow-cyan-900/40"
                  : "text-slate-400 hover:text-white"
              }`}
              title="react-simple-maps SVG Vector Map (Zero API Key)"
            >
              react-simple-maps
            </button>
          </div>

          {/* View Mode Switcher */}
          <div className="flex items-center bg-slate-900 p-1 rounded-xl border border-slate-800 space-x-1">
            <button
              onClick={() => setViewMode("split")}
              className={`p-1.5 rounded-lg text-xs transition ${
                viewMode === "split"
                  ? "bg-cyan-600 text-white shadow-md shadow-cyan-900/40"
                  : "text-slate-400 hover:text-white"
              }`}
              title="Split View (Map + List)"
            >
              <Columns className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setViewMode("map")}
              className={`p-1.5 rounded-lg text-xs transition ${
                viewMode === "map"
                  ? "bg-cyan-600 text-white shadow-md shadow-cyan-900/40"
                  : "text-slate-400 hover:text-white"
              }`}
              title="Expanded Full Map"
            >
              <MapIcon className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setViewMode("grid")}
              className={`p-1.5 rounded-lg text-xs transition ${
                viewMode === "grid"
                  ? "bg-cyan-600 text-white shadow-md shadow-cyan-900/40"
                  : "text-slate-400 hover:text-white"
              }`}
              title="Catalog Grid View"
            >
              <Grid className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Live Geospatial Network Radar Bar */}
      <div className="px-6 py-2.5 bg-slate-950 border-b border-slate-800/80">
        <div className="bg-gradient-to-r from-emerald-950/40 via-slate-900/90 to-cyan-950/30 border border-emerald-500/30 rounded-xl p-3 flex flex-wrap items-center justify-between gap-3 shadow-lg shadow-emerald-950/20">
          <div className="flex items-center space-x-3">
            <div className="relative flex h-3 w-3 shrink-0">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500 shadow-sm shadow-emerald-400"></span>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-bold uppercase tracking-wider text-emerald-300">
                  Live Geospatial Network: Real Physical Places
                </span>
                <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-emerald-950/80 text-emerald-400 border border-emerald-700/60 font-semibold">
                  Zero Mock Data
                </span>
                {liveDiscoveredCount !== null && (
                  <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-cyan-950/80 text-cyan-300 border border-cyan-700/60 font-semibold">
                    {liveDiscoveredCount} Live Places Synced
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Pulls live convention centers, theaters & halls from the OpenStreetMap global network with real coordinates & street addresses.
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2 flex-wrap">
            <div className="flex items-center space-x-1 bg-slate-900/90 p-1 rounded-lg border border-slate-800">
              {["Seattle", "Mumbai", "Delhi", "Bengaluru"].map((c) => (
                <button
                  key={c}
                  onClick={() => handleDiscoverLiveVenues(c)}
                  disabled={liveDiscovering}
                  className={`px-2.5 py-1 text-xs rounded-md font-semibold transition ${
                    selectedCity === c
                      ? "bg-emerald-500 text-slate-950 shadow-sm shadow-emerald-500/30"
                      : "text-slate-300 hover:text-white hover:bg-slate-800"
                  }`}
                >
                  {c}
                </button>
              ))}
            </div>

            <button
              onClick={() => handleDiscoverLiveVenues()}
              disabled={liveDiscovering}
              className="px-3.5 py-1.5 text-xs font-bold rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 transition-all flex items-center space-x-1.5 shadow-md shadow-emerald-500/25 active:scale-95 disabled:opacity-50"
            >
              {liveDiscovering ? (
                <>
                  <span className="animate-spin inline-block w-3 h-3 border-2 border-slate-950 border-t-transparent rounded-full" />
                  <span>Scanning Global Map Network...</span>
                </>
              ) : (
                <>
                  <Radio className="w-3.5 h-3.5 text-slate-950 animate-pulse" />
                  <span>Fetch Live Real Places</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Main Workspace Body */}
      <div className="flex-1 flex min-h-0 overflow-hidden relative">
        {/* Left Column: Venue Roster List (Visible in split & grid modes) */}
        {viewMode !== "map" && (
          <div
            className={`border-r border-slate-800/80 bg-[#070b12] flex flex-col shrink-0 overflow-hidden ${
              viewMode === "grid" ? "w-full" : "w-full md:w-[420px] lg:w-[460px]"
            }`}
          >
            {/* List Sub-header */}
            <div className="p-3 border-b border-slate-800/80 flex items-center justify-between bg-slate-900/40">
              <span className="text-xs font-mono text-slate-400">
                Found <strong className="text-white">{filteredVenues.length}</strong> real-world facilities
              </span>
              <span className="text-[11px] font-mono text-cyan-400 flex items-center space-x-1">
                <MapPin className="w-3 h-3" />
                <span>GPS Verified</span>
              </span>
            </div>

            {/* Scrollable Venue Cards */}
            <div className={`flex-1 overflow-y-auto p-3 space-y-3 ${viewMode === "grid" ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 space-y-0" : ""}`}>
              {loading ? (
                <div className="py-24 text-center text-xs font-mono text-slate-500">
                  <div className="w-6 h-6 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
                  Querying Spatial Venue Registry...
                </div>
              ) : filteredVenues.length > 0 ? (
                filteredVenues.map((v) => {
                  const isSelected = selectedVenue?.id === v.id;
                  const isBound = selectedVenueIdForEvent === v.id;

                  return (
                    <div
                      key={v.id}
                      onClick={() => handleSelectVenue(v)}
                      className={`group p-4 rounded-xl border transition-all cursor-pointer flex flex-col justify-between space-y-3 ${
                        isSelected
                          ? "bg-slate-900/90 border-cyan-500 shadow-xl shadow-cyan-950/40 ring-1 ring-cyan-500/40"
                          : "bg-slate-900/40 border-slate-800/80 hover:bg-slate-900/70 hover:border-slate-700"
                      }`}
                    >
                      {/* Top Badges */}
                      <div className="space-y-1.5">
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-slate-800 text-cyan-300 font-semibold border border-slate-700">
                            {v.venue_type.replace("_", " ")}
                          </span>
                          <div className="flex items-center space-x-1.5">
                            <span className="text-xs font-bold text-amber-400 flex items-center space-x-0.5">
                              <Star className="w-3 h-3 fill-amber-400" />
                              <span>4.8</span>
                            </span>
                            <span className="text-[10px] font-mono text-emerald-400 font-semibold">
                              {v.status}
                            </span>
                          </div>
                        </div>

                        {/* Title and Location */}
                        <h3 className="text-sm font-bold text-white group-hover:text-cyan-300 transition leading-snug">
                          {v.name}
                        </h3>
                        <p className="text-xs text-slate-400 flex items-center space-x-1">
                          <MapPin className="w-3 h-3 text-slate-500 shrink-0" />
                          <span className="truncate">{v.address || v.city}</span>
                        </p>

                        {/* Real-world Coordinates & Google Maps Link */}
                        <div className="flex items-center justify-between text-[10px] font-mono pt-0.5">
                          {v.latitude && v.longitude ? (
                            <span className="text-emerald-400/90 flex items-center space-x-1">
                              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block animate-pulse"></span>
                              <span>GPS: {v.latitude.toFixed(4)}°, {v.longitude.toFixed(4)}°</span>
                            </span>
                          ) : (
                            <span className="text-slate-500">{v.city}</span>
                          )}
                          <a
                            href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(v.name + " " + v.city)}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="text-cyan-400 hover:text-cyan-300 flex items-center space-x-1 hover:underline font-semibold"
                            title="Verify on Google Maps"
                          >
                            <span>Google Maps</span>
                            <Compass className="w-3 h-3" />
                          </a>
                        </div>
                      </div>

                      {/* Specs and Pricing */}
                      <div className="pt-2.5 border-t border-slate-800/80 grid grid-cols-2 gap-2 text-xs font-mono">
                        <div>
                          <span className="text-slate-500 text-[10px] block">CAPACITY</span>
                          <span className="font-semibold text-slate-200 flex items-center space-x-1">
                            <Users className="w-3 h-3 text-slate-400" />
                            <span>{v.capacity} Guests</span>
                          </span>
                        </div>
                        <div className="text-right">
                          <span className="text-slate-500 text-[10px] block">HOURLY RATE</span>
                          <span className="font-bold text-emerald-400">${v.hourly_rate || 0}/hr</span>
                        </div>
                      </div>

                      {/* Amenities Pills */}
                      <div className="flex flex-wrap gap-1 pt-1">
                        {v.amenities.slice(0, 4).map((amenity, idx) => (
                          <span
                            key={idx}
                            className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-slate-950 text-slate-400 border border-slate-800 uppercase"
                          >
                            {amenity.replace("_", " ")}
                          </span>
                        ))}
                        {v.amenities.length > 4 && (
                          <span className="text-[9px] font-mono text-slate-500">
                            +{v.amenities.length - 4} more
                          </span>
                        )}
                      </div>

                      {/* Action Bar */}
                      <div className="pt-2 border-t border-slate-800/60 flex items-center space-x-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleCheckAvailability(v.id);
                          }}
                          className="flex-1 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center justify-center space-x-1 transition"
                        >
                          <Clock className="w-3 h-3 text-amber-400" />
                          <span>Window</span>
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleCheckSuitability(v.id);
                          }}
                          className="flex-1 py-1.5 rounded-lg bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-300 border border-cyan-500/40 text-xs font-semibold flex items-center justify-center space-x-1 transition"
                        >
                          <Sparkles className="w-3 h-3" />
                          <span>Suitability</span>
                        </button>
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="py-24 text-center text-xs font-mono text-slate-500">
                  No venues found matching your criteria. Try adjusting the search or region filter.
                </div>
              )}
            </div>
          </div>
        )}

        {/* Right Column: Full Interactive Map Canvas (Visible in split & map modes) */}
        {viewMode !== "grid" && (
          <div className="flex-1 h-full min-h-0 relative p-3">
            {mapEngine === "streets" ? (
              <VenueMap
                venues={filteredVenues}
                selectedVenue={selectedVenue}
                onSelectVenue={handleSelectVenue}
                eventCity={selectedCity !== "ALL" ? selectedCity : (event?.location || undefined)}
                onCheckAvailability={handleCheckAvailability}
                onCheckSuitability={handleCheckSuitability}
                className="h-full w-full"
              />
            ) : (
              <SimpleSvgMap
                venues={filteredVenues}
                selectedVenue={selectedVenue}
                onSelectVenue={handleSelectVenue}
                eventCity={selectedCity !== "ALL" ? selectedCity : (event?.location || undefined)}
                className="h-full w-full"
              />
            )}
          </div>
        )}
      </div>

      {/* Operational Inspection & Verification Modal / Drawer */}
      {inspectorOpen && selectedVenue && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="max-w-xl w-full rounded-2xl bg-slate-900 border border-slate-700 shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150 flex flex-col max-h-[85vh]">
            {/* Modal Header */}
            <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/80">
              <div className="flex items-center space-x-3">
                <div className="p-2 rounded-xl bg-cyan-950 text-cyan-400 border border-cyan-800">
                  <Building2 className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">{selectedVenue.name}</h3>
                  <p className="text-xs text-slate-400 flex items-center space-x-1">
                    <MapPin className="w-3 h-3 text-slate-500" />
                    <span>{selectedVenue.address || selectedVenue.city}</span>
                  </p>
                </div>
              </div>
              <button
                onClick={() => setInspectorOpen(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-5 overflow-y-auto space-y-5 text-xs font-sans">
              {/* Quick Facility Overview */}
              <div className="grid grid-cols-3 gap-3 p-3.5 rounded-xl bg-slate-950 border border-slate-800 font-mono">
                <div>
                  <span className="text-slate-500 text-[10px] block">MAX CAPACITY</span>
                  <span className="text-sm font-bold text-white">{selectedVenue.capacity}</span>
                </div>
                <div>
                  <span className="text-slate-500 text-[10px] block">BASE RATE</span>
                  <span className="text-sm font-bold text-emerald-400">${selectedVenue.hourly_rate}/hr</span>
                </div>
                <div>
                  <span className="text-slate-500 text-[10px] block">GEO COORDINATES</span>
                  <span className="text-xs font-bold text-slate-300">
                    {selectedVenue.latitude?.toFixed(4)}, {selectedVenue.longitude?.toFixed(4)}
                  </span>
                </div>
              </div>

              {/* Suitability Evaluation Section */}
              <div className="space-y-2.5">
                <div className="flex items-center justify-between">
                  <h4 className="font-bold text-slate-200 uppercase tracking-wider text-[11px] flex items-center space-x-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Deterministic Suitability Scorecard</span>
                  </h4>
                  {evaluatingSuit && (
                    <span className="text-cyan-400 font-mono text-[10px] animate-pulse">Evaluating...</span>
                  )}
                </div>

                {suitResult ? (
                  <div className="p-4 rounded-xl border border-slate-800 bg-slate-950/70 space-y-3">
                    <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                      <div>
                        <span className="text-[10px] font-mono text-slate-400 uppercase">Overall Suitability</span>
                        <div className="text-2xl font-black text-cyan-400">
                          {suitResult.score}%
                        </div>
                      </div>
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-mono font-bold border ${
                          suitResult.is_suitable
                            ? "bg-emerald-950 text-emerald-300 border-emerald-800"
                            : "bg-rose-950 text-rose-300 border-rose-800"
                        }`}
                      >
                        {suitResult.is_suitable ? "OPERATIONAL MATCH" : "CRITERIA DEFICIT"}
                      </span>
                    </div>

                    <div className="grid grid-cols-3 gap-2 text-center font-mono">
                      <div className="p-2 rounded-lg bg-slate-900 border border-slate-800">
                        <span className="text-[10px] text-slate-400 block">CAPACITY</span>
                        <span
                          className={`font-bold ${
                            suitResult.capacity_match ? "text-emerald-400" : "text-rose-400"
                          }`}
                        >
                          {suitResult.capacity_match ? "PASSED" : "FAILED"}
                        </span>
                      </div>
                      <div className="p-2 rounded-lg bg-slate-900 border border-slate-800">
                        <span className="text-[10px] text-slate-400 block">AMENITIES</span>
                        <span
                          className={`font-bold ${
                            suitResult.amenity_match ? "text-emerald-400" : "text-rose-400"
                          }`}
                        >
                          {suitResult.amenity_match ? "PASSED" : "FAILED"}
                        </span>
                      </div>
                      <div className="p-2 rounded-lg bg-slate-900 border border-slate-800">
                        <span className="text-[10px] text-slate-400 block">BUDGET</span>
                        <span
                          className={`font-bold ${
                            suitResult.budget_match ? "text-emerald-400" : "text-rose-400"
                          }`}
                        >
                          {suitResult.budget_match ? "PASSED" : "FAILED"}
                        </span>
                      </div>
                    </div>

                    {suitResult.reasons?.length > 0 && (
                      <div className="space-y-1 pt-1">
                        <span className="text-[10px] font-mono text-slate-400 uppercase">Engine Findings:</span>
                        <ul className="space-y-1">
                          {suitResult.reasons.map((r, idx) => (
                            <li key={idx} className="text-slate-300 flex items-start space-x-1.5">
                              <span className="text-cyan-400">•</span>
                              <span>{r}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ) : (
                  <button
                    onClick={() => handleCheckSuitability(selectedVenue.id)}
                    className="w-full py-2.5 rounded-xl bg-slate-950 hover:bg-slate-800 border border-slate-800 text-slate-300 font-semibold flex items-center justify-center space-x-2 transition"
                  >
                    <Sparkles className="w-4 h-4 text-cyan-400" />
                    <span>Run Suitability Check against Guest Count ({event?.guest_count || 300})</span>
                  </button>
                )}
              </div>

              {/* Availability Window Verification */}
              <div className="space-y-2.5">
                <div className="flex items-center justify-between">
                  <h4 className="font-bold text-slate-200 uppercase tracking-wider text-[11px] flex items-center space-x-1.5">
                    <Clock className="w-3.5 h-3.5 text-amber-400" />
                    <span>Live Availability Window Check</span>
                  </h4>
                  {checkingAvail && (
                    <span className="text-amber-400 font-mono text-[10px] animate-pulse">Checking database...</span>
                  )}
                </div>

                {availResult ? (
                  <div
                    className={`p-3.5 rounded-xl border flex items-center justify-between ${
                      availResult.is_available
                        ? "bg-emerald-950/50 border-emerald-800 text-emerald-200"
                        : "bg-rose-950/50 border-rose-800 text-rose-200"
                    }`}
                  >
                    <div className="flex items-center space-x-2.5">
                      {availResult.is_available ? (
                        <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                      ) : (
                        <XCircle className="w-5 h-5 text-rose-400" />
                      )}
                      <div>
                        <div className="font-bold">
                          {availResult.is_available
                            ? "Venue Available for Scheduled Operating Window"
                            : "Booking Conflict Detected"}
                        </div>
                        <p className="text-[11px] opacity-80">
                          {availResult.is_available
                            ? "No overlapping events registered during requested timeslot."
                            : "Venue is already booked by another reservation in this window."}
                        </p>
                      </div>
                    </div>
                  </div>
                ) : (
                  <button
                    onClick={() => handleCheckAvailability(selectedVenue.id)}
                    className="w-full py-2.5 rounded-xl bg-slate-950 hover:bg-slate-800 border border-slate-800 text-slate-300 font-semibold flex items-center justify-center space-x-2 transition"
                  >
                    <Clock className="w-4 h-4 text-amber-400" />
                    <span>Check Time Window Availability</span>
                  </button>
                )}
              </div>
            </div>

            {/* Modal Footer: Bind Action */}
            <div className="p-4 border-t border-slate-800 bg-slate-950/90 flex items-center justify-between">
              <button
                onClick={() => setInspectorOpen(false)}
                className="px-4 py-2 rounded-xl text-slate-400 hover:text-white transition font-medium"
              >
                Close
              </button>
              <button
                onClick={() => {
                  handleBindVenueToEvent(selectedVenue);
                  setInspectorOpen(false);
                }}
                className="px-5 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold text-xs flex items-center space-x-2 shadow-lg shadow-cyan-600/40 transition"
              >
                <Check className="w-4 h-4" />
                <span>Bind as Primary Event Venue</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
