"use client";

import React, { useState, useEffect, useMemo } from "react";
import { useParams } from "next/navigation";
import dynamic from "next/dynamic";
import { searchVenues, checkVenueAvailability, checkVenueSuitability, discoverVenues } from "../../../../lib/api/venues";
import { discoverProvidersForEvent, createAssignment, getAssignmentsForEvent } from "../../../../lib/api/vendors";
import { useEvent } from "../../../../hooks/useEvent";
import type {
  VenueResponse,
  VendorResponse,
  DiscoveryMapEntity,
  VenueAvailabilityResult,
  VenueSuitabilityResult,
} from "../../../../types/api";

import {
  Building2,
  Search,
  Users,
  MapPin,
  CheckCircle2,
  XCircle,
  Clock,
  Sparkles,
  Columns,
  Grid,
  Map as MapIcon,
  Compass,
  Star,
  Check,
  Radio,
  X,
  Camera,
  Utensils,
  Volume2,
  Flower2,
  Music,
  Shield,
  Package,
  Plus,
  Navigation,
  ExternalLink,
  Phone,
  Globe,
  SlidersHorizontal,
} from "lucide-react";

// Dynamically import Leaflet DiscoveryMap with SSR disabled
const DiscoveryMap = dynamic(() => import("../../../../components/maps/DiscoveryMap"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full min-h-[500px] flex flex-col items-center justify-center bg-[#090d16] text-slate-400 font-mono text-xs border border-slate-800 rounded-2xl">
      <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin mb-3"></div>
      <span>Loading EVENTRA Operational Map Engine...</span>
    </div>
  ),
});

// Category definition for quick discovery
const DISCOVERY_DOMAINS = [
  { key: "VENUE", label: "Venues & Spaces", icon: Building2, defaultCategory: "VENUE" },
  { key: "PHOTOGRAPHY", label: "Photography", icon: Camera, defaultCategory: "PHOTOGRAPHY" },
  { key: "CATERING", label: "Catering", icon: Utensils, defaultCategory: "CATERING" },
  { key: "AV_TECH", label: "AV & Sound", icon: Volume2, defaultCategory: "AV_TECH" },
  { key: "DECOR", label: "Decor & Floral", icon: Flower2, defaultCategory: "DECOR" },
  { key: "DJ_MUSIC", label: "DJ & Music", icon: Music, defaultCategory: "DJ_MUSIC" },
  { key: "SECURITY", label: "Security", icon: Shield, defaultCategory: "SECURITY" },
  { key: "RENTALS", label: "Rentals", icon: Package, defaultCategory: "RENTALS" },
];

export default function PhysicalNetworkDiscoveryPage() {
  const params = useParams();
  const eventId = params?.eventId as string;

  const { event, specification } = useEvent(eventId);

  // Active Category Domain (Default: VENUE or requirement)
  const [activeDomain, setActiveDomain] = useState<string>("VENUE");

  // Search, Location & Anchor Mode State
  const [searchQuery, setSearchQuery] = useState("");
  const [anchorMode, setAnchorMode] = useState<"NEAR_EVENT" | "NEAR_ME" | "REGION">("NEAR_EVENT");
  const [selectedCity, setSelectedCity] = useState<string>("Seattle");
  const [radiusKm, setRadiusKm] = useState<number | undefined>(undefined);
  const [userCoords, setUserCoords] = useState<[number, number] | null>(null);

  // Unified Map Entities
  const [places, setPlaces] = useState<DiscoveryMapEntity[]>([]);
  const [selectedPlace, setSelectedPlace] = useState<DiscoveryMapEntity | null>(null);
  const [loading, setLoading] = useState(false);
  const [anchorCoordinates, setAnchorCoordinates] = useState<[number, number] | null>([47.6062, -122.3321]);
  const [anchorLabel, setAnchorLabel] = useState<string | null>("Civic Convention Hall, Seattle");

  // Assigned Vendor IDs for this event
  const [assignedVendorIds, setAssignedVendorIds] = useState<Set<string>>(new Set());

  // View Mode: split (Google Maps style), map-only, list-only
  const [viewMode, setViewMode] = useState<"split" | "map" | "grid">("split");

  // Venue-specific Operational State (Preserving 100% existing functionality)
  const [availResult, setAvailResult] = useState<VenueAvailabilityResult | null>(null);
  const [checkingAvail, setCheckingAvail] = useState(false);
  const [suitResult, setSuitResult] = useState<VenueSuitabilityResult | null>(null);
  const [evaluatingSuit, setEvaluatingSuit] = useState(false);
  const [inspectorOpen, setInspectorOpen] = useState(false);
  const [boundVenueId, setBoundVenueId] = useState<string | null>(null);

  // Notification Toast State
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 4000);
  };

  // Sync event city & fetch assigned vendors on mount
  useEffect(() => {
    if (event?.location) {
      const loc = event.location.toLowerCase();
      if (loc.includes("seattle")) setSelectedCity("Seattle");
      else if (loc.includes("mumbai")) setSelectedCity("Mumbai");
      else if (loc.includes("delhi")) setSelectedCity("Delhi");
      else if (loc.includes("bengaluru")) setSelectedCity("Bengaluru");
      setAnchorLabel(event.location);
    }

    if (eventId) {
      getAssignmentsForEvent(eventId)
        .then((assignments) => {
          const ids = new Set(assignments.map((a) => a.vendor_id));
          setAssignedVendorIds(ids);
        })
        .catch(() => {});
    }
  }, [event, eventId]);

  // Handle User Geolocation for "NEAR_ME"
  const handleSelectNearMe = () => {
    setAnchorMode("NEAR_ME");
    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const coords: [number, number] = [pos.coords.latitude, pos.coords.longitude];
          setUserCoords(coords);
          setAnchorCoordinates(coords);
          setAnchorLabel("Your Device Location");
          executeDiscovery("NEAR_ME", coords, activeDomain);
        },
        (err) => {
          console.warn("Geolocation denied or unavailable:", err);
          showToast("Device location not available. Falling back to Event Location.");
          setAnchorMode("NEAR_EVENT");
        },
        { timeout: 6000 }
      );
    } else {
      showToast("Geolocation not supported by your browser.");
      setAnchorMode("NEAR_EVENT");
    }
  };

  // Convert VenueResponse to DiscoveryMapEntity
  const mapVenueToEntity = (v: VenueResponse): DiscoveryMapEntity => ({
    id: v.id,
    name: v.name,
    entity_type: "VENUE",
    category: "VENUE",
    latitude: v.latitude || 0,
    longitude: v.longitude || 0,
    address: v.address || `${v.city}, WA`,
    city: v.city,
    hourly_rate: v.hourly_rate,
    capacity: v.capacity,
    amenities: v.amenities,
    status: v.status,
    is_assigned: boundVenueId === v.id,
  });

  // Convert VendorResponse to DiscoveryMapEntity
  const mapVendorToEntity = (v: VendorResponse): DiscoveryMapEntity => ({
    id: v.id,
    name: v.name,
    entity_type: "PROVIDER",
    category: v.category,
    latitude: v.latitude || 0,
    longitude: v.longitude || 0,
    address: v.address || v.city,
    city: v.city,
    rating: v.rating,
    review_count: v.review_count,
    distance_km: v.distance_km,
    maps_url: v.maps_url,
    phone: v.phone || v.contact_phone,
    website: v.website,
    hourly_rate: v.hourly_rate || v.base_cost,
    capabilities: v.capabilities,
    status: v.status,
    is_assigned: assignedVendorIds.has(v.id) || v.is_assigned,
  });

  // Primary Execution: Discovers Venues or Providers based on current filters
  const executeDiscovery = async (
    targetAnchorMode = anchorMode,
    customCoords = userCoords,
    targetDomain = activeDomain
  ) => {
    setLoading(true);
    try {
      if (targetDomain === "VENUE") {
        // Venue Discovery
        const cityTarget = targetAnchorMode === "REGION" ? selectedCity : "Seattle";
        const res = await discoverVenues({
          city: cityTarget,
          query: searchQuery.trim() || undefined,
          limit: 30,
          save_to_db: true,
        });

        const venueEntities = (res.items || []).map(mapVenueToEntity);
        setPlaces(venueEntities);
        if (venueEntities.length > 0) setSelectedPlace(venueEntities[0]);
      } else {
        // Provider Discovery
        const res = await discoverProvidersForEvent(eventId, {
          category: targetDomain,
          query: searchQuery.trim() || undefined,
          location: targetAnchorMode === "REGION" ? selectedCity : undefined,
          anchor_mode: targetAnchorMode,
          latitude: targetAnchorMode === "NEAR_ME" && customCoords ? customCoords[0] : undefined,
          longitude: targetAnchorMode === "NEAR_ME" && customCoords ? customCoords[1] : undefined,
          radius_km: radiusKm,
          limit: 30,
        });

        if (res.anchor_coordinates) {
          setAnchorCoordinates(res.anchor_coordinates);
        }
        if (res.anchor_label) {
          setAnchorLabel(res.anchor_label);
        }
        if (res.anchor_mode) {
          const mode = res.anchor_mode as "NEAR_EVENT" | "NEAR_ME" | "REGION";
          setAnchorMode(mode);
          if (mode === "REGION" && res.anchor_label) {
            setSelectedCity(res.anchor_label);
          }
        }

        const providerEntities = (res.items || []).map(mapVendorToEntity);
        setPlaces(providerEntities);
        if (providerEntities.length > 0) setSelectedPlace(providerEntities[0]);
      }
    } catch (err: any) {
      console.error("Discovery failed:", err);
      showToast("Discovery network query failed. Please check network connection.");
    } finally {
      setLoading(false);
    }
  };

  // Run discovery on domain, region, radius change
  useEffect(() => {
    executeDiscovery();
  }, [activeDomain, selectedCity, radiusKm, anchorMode]);

  // Handle Assign to Event
  const handleAssignToEvent = async (place: DiscoveryMapEntity) => {
    try {
      await createAssignment({
        event_id: eventId,
        vendor_id: place.id,
        category: place.category,
        agreed_cost: place.hourly_rate ? place.hourly_rate * 4 : 500,
        notes: `Assigned via EVENTRA Geospatial Discovery from ${place.city}`,
      });

      setAssignedVendorIds((prev) => new Set([...prev, place.id]));

      // Update place locally
      setPlaces((prev) =>
        prev.map((p) => (p.id === place.id ? { ...p, is_assigned: true } : p))
      );
      if (selectedPlace?.id === place.id) {
        setSelectedPlace((prev) => (prev ? { ...prev, is_assigned: true } : null));
      }

      showToast(`✓ Assigned ${place.name} to ${event?.name || "Event"}!`);
    } catch (err: any) {
      console.error("Assignment failed:", err);
      showToast(err?.message || "Failed to assign provider to event.");
    }
  };

  // Venue-specific actions
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

  const handleBindVenue = (place: DiscoveryMapEntity) => {
    setBoundVenueId(place.id);
    setPlaces((prev) =>
      prev.map((p) => (p.id === place.id ? { ...p, is_assigned: true } : p))
    );
    showToast(`✓ "${place.name}" bound as primary operational venue!`);
  };

  // Event requirements list (Venue, Catering, AV, Photography, Security)
  const eventRequirements = [
    { key: "VENUE", label: "Venue", icon: Building2 },
    { key: "CATERING", label: "Catering", icon: Utensils },
    { key: "AV_TECH", label: "AV & Sound", icon: Volume2 },
    { key: "PHOTOGRAPHY", label: "Photography", icon: Camera },
    { key: "SECURITY", label: "Security", icon: Shield },
  ];

  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem)] bg-[#070b12] text-slate-100 overflow-hidden font-sans">
      {/* Toast Notification Alert */}
      {toastMessage && (
        <div className="fixed top-16 right-6 z-50 px-4 py-2.5 rounded-xl bg-emerald-500 text-slate-950 font-bold text-xs shadow-2xl shadow-emerald-500/40 border border-emerald-300 animate-in fade-in slide-in-from-top-3 flex items-center space-x-2">
          <Check className="w-4 h-4" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Top Filter and Controls Bar */}
      <div className="px-4 py-3 border-b border-slate-800/90 bg-[#090d16]/95 backdrop-blur-md flex flex-wrap items-center justify-between gap-3 shrink-0 z-30">
        {/* Title & Live Status */}
        <div className="flex items-center space-x-3">
          <div className="p-1.5 rounded-lg bg-cyan-950 text-cyan-400 border border-cyan-800">
            <Compass className="w-4 h-4" />
          </div>
          <div>
            <h1 className="text-sm font-black tracking-tight text-white flex items-center space-x-2">
              <span>Physical Venue & Provider Network</span>
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 font-semibold">
                Operational Radar
              </span>
            </h1>
          </div>
        </div>

        {/* Global Controls & Natural Language Search */}
        <div className="flex items-center space-x-2 flex-wrap">
          {/* Natural Language / Keyword Search Input */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              executeDiscovery();
            }}
            className="relative w-64 md:w-72"
          >
            <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder='Search e.g. "photographers near venue"...'
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition font-sans"
            />
          </form>

          {/* Location Anchor Mode Selector */}
          <div className="flex items-center bg-slate-900 p-1 rounded-xl border border-slate-800 space-x-1 text-xs font-semibold">
            <button
              onClick={() => {
                setAnchorMode("NEAR_EVENT");
                executeDiscovery("NEAR_EVENT");
              }}
              className={`px-2.5 py-1 rounded-lg transition flex items-center space-x-1 ${
                anchorMode === "NEAR_EVENT"
                  ? "bg-cyan-600 text-white shadow-md shadow-cyan-900/40"
                  : "text-slate-400 hover:text-white"
              }`}
              title="Anchor to Event Venue / Operational Location"
            >
              <MapPin className="w-3 h-3 text-cyan-300" />
              <span>Near Event</span>
            </button>

            <button
              onClick={handleSelectNearMe}
              className={`px-2.5 py-1 rounded-lg transition flex items-center space-x-1 ${
                anchorMode === "NEAR_ME"
                  ? "bg-cyan-600 text-white shadow-md shadow-cyan-900/40"
                  : "text-slate-400 hover:text-white"
              }`}
              title="Anchor to your Browser / Device Location"
            >
              <Navigation className="w-3 h-3 text-cyan-300" />
              <span>Near Me</span>
            </button>

            <button
              onClick={() => {
                setAnchorMode("REGION");
                executeDiscovery("REGION");
              }}
              className={`px-2.5 py-1 rounded-lg transition flex items-center space-x-1 ${
                anchorMode === "REGION"
                  ? "bg-cyan-600 text-white shadow-md shadow-cyan-900/40"
                  : "text-slate-400 hover:text-white"
              }`}
              title="Anchor to Explicit Region / City"
            >
              <Compass className="w-3 h-3 text-cyan-300" />
              <span>Region</span>
            </button>
          </div>

          {/* Explicit Region Selector (Active when REGION selected) */}
          {anchorMode === "REGION" && (
            <select
              value={selectedCity}
              onChange={(e) => setSelectedCity(e.target.value)}
              className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-300 font-semibold focus:outline-none focus:border-cyan-500 animate-in fade-in"
            >
              <option value="Seattle">Seattle, WA</option>
              <option value="Mumbai">Mumbai, MH</option>
              <option value="Delhi">Delhi, NCR</option>
              <option value="Bengaluru">Bengaluru, KA</option>
            </select>
          )}

          {/* Proximity / Radius Filter */}
          <select
            value={radiusKm || ""}
            onChange={(e) => setRadiusKm(e.target.value ? Number(e.target.value) : undefined)}
            className="px-2.5 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-300 font-semibold focus:outline-none focus:border-cyan-500"
            title="Deterministic Proximity Radius"
          >
            <option value="">Any Radius</option>
            <option value="5">Within 5 km</option>
            <option value="10">Within 10 km</option>
            <option value="25">Within 25 km</option>
            <option value="50">Within 50 km</option>
          </select>

          {/* View Mode Switcher */}
          <div className="flex items-center bg-slate-900 p-1 rounded-xl border border-slate-800 space-x-1">
            <button
              onClick={() => setViewMode("split")}
              className={`p-1.5 rounded-lg text-xs transition ${
                viewMode === "split" ? "bg-cyan-600 text-white shadow-md" : "text-slate-400 hover:text-white"
              }`}
              title="Split View (Map + List)"
            >
              <Columns className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setViewMode("map")}
              className={`p-1.5 rounded-lg text-xs transition ${
                viewMode === "map" ? "bg-cyan-600 text-white shadow-md" : "text-slate-400 hover:text-white"
              }`}
              title="Expanded Full Map"
            >
              <MapIcon className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setViewMode("grid")}
              className={`p-1.5 rounded-lg text-xs transition ${
                viewMode === "grid" ? "bg-cyan-600 text-white shadow-md" : "text-slate-400 hover:text-white"
              }`}
              title="Catalog Grid View"
            >
              <Grid className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* KILLER FEATURE BAR: EVENT REQUIREMENTS -> RESOURCE DISCOVERY */}
      <div className="px-4 py-2 bg-slate-950 border-b border-slate-800/80 flex flex-wrap items-center justify-between gap-2 text-xs">
        <div className="flex items-center space-x-2">
          <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 font-bold flex items-center space-x-1">
            <Sparkles className="w-3 h-3" />
            <span>REQUIRED FOR THIS EVENT</span>
          </span>
          <span className="text-slate-400 text-[11px] hidden md:inline">
            1-Click Discovery anchored to {anchorLabel}:
          </span>
        </div>

        <div className="flex items-center space-x-1.5 overflow-x-auto py-0.5">
          {eventRequirements.map((req) => {
            const Icon = req.icon;
            const isSelected = activeDomain === req.key;
            return (
              <button
                key={req.key}
                onClick={() => {
                  setActiveDomain(req.key);
                  setSearchQuery("");
                }}
                className={`px-3 py-1 rounded-xl text-xs font-bold transition flex items-center space-x-1.5 shrink-0 ${
                  isSelected
                    ? "bg-cyan-500 text-slate-950 shadow-lg shadow-cyan-500/30 scale-105"
                    : "bg-slate-900/90 text-slate-300 hover:text-white hover:bg-slate-800 border border-slate-800"
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{req.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Secondary Multi-Category Filter Bar */}
      <div className="px-4 py-1.5 bg-[#090d16] border-b border-slate-800/60 flex items-center space-x-1 overflow-x-auto text-[11px] font-mono">
        <span className="text-slate-500 uppercase px-2 shrink-0">ALL CATEGORIES:</span>
        {DISCOVERY_DOMAINS.map((dom) => {
          const Icon = dom.icon;
          const isSelected = activeDomain === dom.key;
          return (
            <button
              key={dom.key}
              onClick={() => {
                setActiveDomain(dom.key);
                setSearchQuery("");
              }}
              className={`px-2.5 py-0.5 rounded-lg transition flex items-center space-x-1 shrink-0 ${
                isSelected
                  ? "bg-slate-800 text-cyan-300 font-bold border border-cyan-800/80"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
              }`}
            >
              <Icon className="w-3 h-3" />
              <span>{dom.label}</span>
            </button>
          );
        })}
      </div>

      {/* Main Workspace Body */}
      <div className="flex-1 flex min-h-0 overflow-hidden relative">
        {/* Left Column: Discovered Places Roster (Visible in split & grid modes) */}
        {viewMode !== "map" && (
          <div
            className={`border-r border-slate-800/80 bg-[#070b12] flex flex-col shrink-0 overflow-hidden ${
              viewMode === "grid" ? "w-full" : "w-full md:w-[420px] lg:w-[460px]"
            }`}
          >
            {/* Roster Header */}
            <div className="p-3 border-b border-slate-800/80 flex items-center justify-between bg-slate-900/40">
              <span className="text-xs font-mono text-slate-400">
                Discovered <strong className="text-white">{places.length}</strong> real-world {activeDomain.toLowerCase()} businesses
              </span>
              <span className="text-[11px] font-mono text-emerald-400 flex items-center space-x-1">
                <Radio className="w-3 h-3 animate-pulse" />
                <span>Zero Mock Data</span>
              </span>
            </div>

            {/* Scrollable Place Cards */}
            <div
              className={`flex-1 overflow-y-auto p-3 space-y-3 ${
                viewMode === "grid" ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 space-y-0" : ""
              }`}
            >
              {loading ? (
                <div className="py-24 text-center text-xs font-mono text-slate-500">
                  <div className="w-6 h-6 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
                  Querying EVENTRA Geospatial Discovery Layer...
                </div>
              ) : places.length > 0 ? (
                places.map((place) => {
                  const isSelected = selectedPlace?.id === place.id;
                  const isAssigned = place.is_assigned;

                  return (
                    <div
                      key={place.id}
                      onClick={() => setSelectedPlace(place)}
                      className={`group p-4 rounded-xl border transition-all cursor-pointer flex flex-col justify-between space-y-3 ${
                        isSelected
                          ? "bg-slate-900/95 border-cyan-500 shadow-xl shadow-cyan-950/40 ring-1 ring-cyan-500/40"
                          : "bg-slate-900/40 border-slate-800/80 hover:bg-slate-900/70 hover:border-slate-700"
                      }`}
                    >
                      {/* Top Badges: Category & Rating */}
                      <div className="space-y-1.5">
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-slate-800 text-cyan-300 font-semibold border border-slate-700">
                            {place.category.replace("_", " ")}
                          </span>

                          <div className="flex items-center space-x-2">
                            {place.rating ? (
                              <span className="text-xs font-bold text-amber-400 flex items-center space-x-0.5 font-mono">
                                <Star className="w-3 h-3 fill-amber-400" />
                                <span>{place.rating.toFixed(1)}</span>
                                {place.review_count && (
                                  <span className="text-[10px] text-slate-400 font-normal">
                                    ({place.review_count})
                                  </span>
                                )}
                              </span>
                            ) : null}

                            {isAssigned && (
                              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 font-bold flex items-center space-x-1">
                                <Check className="w-3 h-3 text-emerald-400" />
                                <span>ASSIGNED</span>
                              </span>
                            )}
                          </div>
                        </div>

                        {/* Title and Location */}
                        <h3 className="text-sm font-bold text-white group-hover:text-cyan-300 transition leading-snug">
                          {place.name}
                        </h3>
                        <p className="text-xs text-slate-400 flex items-center space-x-1">
                          <MapPin className="w-3 h-3 text-slate-500 shrink-0" />
                          <span className="truncate">{place.address || place.city}</span>
                        </p>

                        {/* Distance & Google Maps Link */}
                        <div className="flex items-center justify-between text-[10px] font-mono pt-0.5">
                          {place.distance_km !== null && place.distance_km !== undefined ? (
                            <span className="text-cyan-300 font-semibold flex items-center space-x-1">
                              <span>📍 {place.distance_km.toFixed(1)} km from Anchor</span>
                            </span>
                          ) : (
                            <span className="text-slate-500">{place.city}</span>
                          )}

                          <a
                            href={
                              place.maps_url ||
                              `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
                                place.name + " " + place.city
                              )}`
                            }
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="text-cyan-400 hover:text-cyan-300 flex items-center space-x-1 hover:underline font-semibold"
                            title="Verify on Google Maps"
                          >
                            <span>Google Maps</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        </div>
                      </div>

                      {/* Hourly Rate or Capacity */}
                      <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs font-mono">
                        {place.entity_type === "VENUE" ? (
                          <div>
                            <span className="text-slate-500 text-[10px] block">CAPACITY</span>
                            <span className="font-semibold text-slate-200">{place.capacity || 300} Guests</span>
                          </div>
                        ) : (
                          <div>
                            <span className="text-slate-500 text-[10px] block">RATE</span>
                            <span className={place.hourly_rate ? "font-bold text-emerald-400" : "text-slate-400 text-xs italic"}>
                              {place.hourly_rate ? `$${Math.round(place.hourly_rate)}/hr` : "Rate unavailable"}
                            </span>
                          </div>
                        )}

                        {/* Primary Action Button: Assign to Event */}
                        <div>
                          {place.entity_type === "PROVIDER" ? (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleAssignToEvent(place);
                              }}
                              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition flex items-center space-x-1 shadow-md ${
                                isAssigned
                                  ? "bg-emerald-950/80 text-emerald-300 border border-emerald-800 hover:bg-emerald-900"
                                  : "bg-cyan-600 hover:bg-cyan-500 text-slate-950 shadow-cyan-600/30 active:scale-95"
                              }`}
                            >
                              {isAssigned ? (
                                <>
                                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                                  <span>✓ Assigned</span>
                                </>
                              ) : (
                                <>
                                  <Plus className="w-3.5 h-3.5 text-slate-950 font-black" />
                                  <span>Assign to Event</span>
                                </>
                              )}
                            </button>
                          ) : (
                            <div className="flex items-center space-x-1">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleCheckAvailability(place.id);
                                }}
                                className="px-2 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
                              >
                                Window
                              </button>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleCheckSuitability(place.id);
                                }}
                                className="px-2 py-1 rounded-lg bg-cyan-600/30 hover:bg-cyan-600/40 text-cyan-300 text-xs font-semibold"
                              >
                                Suitability
                              </button>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleBindVenue(place);
                                }}
                                className="px-2 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs"
                              >
                                Bind
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="py-24 text-center text-xs font-mono text-slate-500 space-y-2">
                  <p>No places found matching your search criteria in this radius.</p>
                  <button
                    onClick={() => {
                      setRadiusKm(undefined);
                      setSearchQuery("");
                      executeDiscovery();
                    }}
                    className="px-3 py-1.5 rounded-lg bg-cyan-900/50 hover:bg-cyan-800/60 text-cyan-300 text-xs font-bold transition"
                  >
                    Expand Search Radius
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Right Column: Interactive Discovery Map */}
        {viewMode !== "grid" && (
          <div className="flex-1 h-full min-h-0 relative p-3">
            <DiscoveryMap
              places={places}
              selectedPlace={selectedPlace}
              onSelectPlace={(p) => setSelectedPlace(p)}
              anchorCoordinates={anchorCoordinates}
              anchorLabel={anchorLabel}
              eventCity={selectedCity}
              className="h-full w-full"
              onAssignToEvent={handleAssignToEvent}
              onCheckAvailability={handleCheckAvailability}
              onCheckSuitability={handleCheckSuitability}
              onBindVenue={handleBindVenue}
            />
          </div>
        )}
      </div>

      {/* Venue Operational Inspection Modal */}
      {inspectorOpen && selectedPlace && selectedPlace.entity_type === "VENUE" && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="max-w-xl w-full rounded-2xl bg-slate-900 border border-slate-700 shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150 flex flex-col max-h-[85vh]">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/80">
              <div className="flex items-center space-x-3">
                <div className="p-2 rounded-xl bg-cyan-950 text-cyan-400 border border-cyan-800">
                  <Building2 className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">{selectedPlace.name}</h3>
                  <p className="text-xs text-slate-400 flex items-center space-x-1">
                    <MapPin className="w-3 h-3 text-slate-500" />
                    <span>{selectedPlace.address}</span>
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

            <div className="p-5 overflow-y-auto space-y-5 text-xs font-sans">
              <div className="grid grid-cols-3 gap-3 p-3.5 rounded-xl bg-slate-950 border border-slate-800 font-mono">
                <div>
                  <span className="text-slate-500 text-[10px] block">CAPACITY</span>
                  <span className="text-sm font-bold text-white">{selectedPlace.capacity || 300}</span>
                </div>
                <div>
                  <span className="text-slate-500 text-[10px] block">RATE</span>
                  <span className="text-sm font-bold text-emerald-400">${selectedPlace.hourly_rate || 500}/hr</span>
                </div>
                <div>
                  <span className="text-slate-500 text-[10px] block">COORDINATES</span>
                  <span className="text-xs font-bold text-slate-300">
                    {selectedPlace.latitude?.toFixed(4)}, {selectedPlace.longitude?.toFixed(4)}
                  </span>
                </div>
              </div>

              {/* Suitability Scorecard */}
              <div className="space-y-2.5">
                <h4 className="font-bold text-slate-200 uppercase tracking-wider text-[11px] flex items-center space-x-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Suitability Scorecard</span>
                </h4>

                {suitResult ? (
                  <div className="p-4 rounded-xl border border-slate-800 bg-slate-950/70 space-y-3">
                    <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                      <div>
                        <span className="text-[10px] font-mono text-slate-400 uppercase">Match Score</span>
                        <div className="text-2xl font-black text-cyan-400">{suitResult.score}%</div>
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
                        <span className={suitResult.capacity_match ? "text-emerald-400 font-bold" : "text-rose-400 font-bold"}>
                          {suitResult.capacity_match ? "PASSED" : "FAILED"}
                        </span>
                      </div>
                      <div className="p-2 rounded-lg bg-slate-900 border border-slate-800">
                        <span className="text-[10px] text-slate-400 block">AMENITIES</span>
                        <span className={suitResult.amenity_match ? "text-emerald-400 font-bold" : "text-rose-400 font-bold"}>
                          {suitResult.amenity_match ? "PASSED" : "FAILED"}
                        </span>
                      </div>
                      <div className="p-2 rounded-lg bg-slate-900 border border-slate-800">
                        <span className="text-[10px] text-slate-400 block">BUDGET</span>
                        <span className={suitResult.budget_match ? "text-emerald-400 font-bold" : "text-rose-400 font-bold"}>
                          {suitResult.budget_match ? "PASSED" : "FAILED"}
                        </span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <button
                    onClick={() => handleCheckSuitability(selectedPlace.id)}
                    className="w-full py-2.5 rounded-xl bg-slate-950 hover:bg-slate-800 border border-slate-800 text-slate-300 font-semibold flex items-center justify-center space-x-2 transition"
                  >
                    <Sparkles className="w-4 h-4 text-cyan-400" />
                    <span>Run Suitability Check</span>
                  </button>
                )}
              </div>

              {/* Availability Window */}
              <div className="space-y-2.5">
                <h4 className="font-bold text-slate-200 uppercase tracking-wider text-[11px] flex items-center space-x-1.5">
                  <Clock className="w-3.5 h-3.5 text-amber-400" />
                  <span>Availability Window</span>
                </h4>

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
                          {availResult.is_available ? "Venue Available for Window" : "Booking Conflict Detected"}
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <button
                    onClick={() => handleCheckAvailability(selectedPlace.id)}
                    className="w-full py-2.5 rounded-xl bg-slate-950 hover:bg-slate-800 border border-slate-800 text-slate-300 font-semibold flex items-center justify-center space-x-2 transition"
                  >
                    <Clock className="w-4 h-4 text-amber-400" />
                    <span>Check Time Window Availability</span>
                  </button>
                )}
              </div>
            </div>

            <div className="p-4 border-t border-slate-800 bg-slate-950/90 flex items-center justify-between">
              <button
                onClick={() => setInspectorOpen(false)}
                className="px-4 py-2 rounded-xl text-slate-400 hover:text-white transition font-medium"
              >
                Close
              </button>
              <button
                onClick={() => {
                  handleBindVenue(selectedPlace);
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
