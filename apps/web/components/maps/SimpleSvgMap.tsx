"use client";

import React, { useState } from "react";
import {
  ComposableMap,
  Geographies,
  Geography,
  Marker,
  ZoomableGroup,
} from "react-simple-maps";
import type { VenueResponse } from "../../types/api";
import {
  MapPin,
  Users,
  DollarSign,
  Maximize2,
  ZoomIn,
  ZoomOut,
  Compass,
  CheckCircle,
} from "lucide-react";

const GEO_URL = "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json";

interface SimpleSvgMapProps {
  venues: VenueResponse[];
  selectedVenue: VenueResponse | null;
  onSelectVenue: (venue: VenueResponse) => void;
  eventCity?: string;
  className?: string;
}

export default function SimpleSvgMap({
  venues,
  selectedVenue,
  onSelectVenue,
  eventCity,
  className = "",
}: SimpleSvgMapProps) {
  const [position, setPosition] = useState<{ coordinates: [number, number]; zoom: number }>({
    coordinates: [-100, 40], // Default US / Seattle view
    zoom: 2.5,
  });

  const [hoveredVenue, setHoveredVenue] = useState<VenueResponse | null>(null);

  const validVenues = venues.filter(
    (v) => typeof v.latitude === "number" && typeof v.longitude === "number"
  );

  const handleZoomIn = () => {
    setPosition((pos) => ({ ...pos, zoom: Math.min(pos.zoom * 1.5, 8) }));
  };

  const handleZoomOut = () => {
    setPosition((pos) => ({ ...pos, zoom: Math.max(pos.zoom / 1.5, 1) }));
  };

  const handleFlyTo = (coords: [number, number], zoom: number = 4) => {
    setPosition({ coordinates: coords, zoom });
  };

  return (
    <div
      className={`relative w-full h-full rounded-2xl overflow-hidden border border-slate-800 bg-[#080d1a] shadow-2xl flex flex-col ${className}`}
    >
      {/* Map Header / Region Quick-Jumps */}
      <div className="absolute top-3 left-3 right-3 z-20 flex items-center justify-between pointer-events-none">
        <div className="flex items-center space-x-1.5 bg-[#090d16]/90 backdrop-blur-md p-1.5 rounded-xl border border-slate-800 shadow-lg pointer-events-auto">
          <span className="text-[10px] font-mono uppercase px-2 text-cyan-400 font-bold flex items-center space-x-1">
            <Compass className="w-3 h-3 text-cyan-400" />
            <span>SVG Maps Engine</span>
          </span>
          <button
            onClick={() => handleFlyTo([-122.33, 47.61], 5)}
            className="px-2.5 py-1 rounded-lg text-[11px] font-semibold text-slate-300 hover:text-white hover:bg-slate-800 transition"
          >
            Seattle
          </button>
          <button
            onClick={() => handleFlyTo([72.87, 19.07], 4.5)}
            className="px-2.5 py-1 rounded-lg text-[11px] font-semibold text-slate-300 hover:text-white hover:bg-slate-800 transition"
          >
            Mumbai
          </button>
          <button
            onClick={() => handleFlyTo([77.20, 28.61], 4.5)}
            className="px-2.5 py-1 rounded-lg text-[11px] font-semibold text-slate-300 hover:text-white hover:bg-slate-800 transition"
          >
            Delhi
          </button>
          <button
            onClick={() => handleFlyTo([77.59, 12.97], 4.5)}
            className="px-2.5 py-1 rounded-lg text-[11px] font-semibold text-slate-300 hover:text-white hover:bg-slate-800 transition"
          >
            Bengaluru
          </button>
        </div>

        {/* Zoom Controls */}
        <div className="flex items-center space-x-1 bg-[#090d16]/90 backdrop-blur-md p-1 rounded-xl border border-slate-800 shadow-lg pointer-events-auto">
          <button
            onClick={handleZoomIn}
            className="p-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition"
            title="Zoom In"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            onClick={handleZoomOut}
            className="p-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition"
            title="Zoom Out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <button
            onClick={() => setPosition({ coordinates: [0, 20], zoom: 1 })}
            className="p-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition"
            title="Reset View"
          >
            <Maximize2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* SVG Canvas via react-simple-maps */}
      <div className="w-full h-full flex-1">
        <ComposableMap
          projection="geoMercator"
          style={{ width: "100%", height: "100%" }}
        >
          <ZoomableGroup
            zoom={position.zoom}
            center={position.coordinates}
            onMoveEnd={(pos) => {
              if (pos.coordinates) {
                setPosition({ coordinates: pos.coordinates, zoom: pos.zoom ?? 1 });
              }
            }}
          >
            <Geographies geography={GEO_URL}>
              {({ geographies }) =>
                geographies.map((geo) => (
                  <Geography
                    key={geo.rsmKey}
                    geography={geo}
                    fill="#10192a"
                    stroke="#1e293b"
                    strokeWidth={0.5}
                    className="hover:fill-[#172554] transition outline-none cursor-pointer"
                  />
                ))
              }
            </Geographies>

            {/* Venue Markers */}
            {validVenues.map((v) => {
              const lng = v.longitude as number;
              const lat = v.latitude as number;
              const isSelected = selectedVenue?.id === v.id;

              return (
                <Marker
                  key={v.id}
                  coordinates={[lng, lat]}
                  onClick={() => onSelectVenue(v)}
                  onMouseEnter={() => setHoveredVenue(v)}
                  onMouseLeave={() => setHoveredVenue(null)}
                >
                  <g className="cursor-pointer">
                    {/* Pulsing ring when selected */}
                    {isSelected && (
                      <circle
                        r={14}
                        fill="none"
                        stroke="#06b6d4"
                        strokeWidth={2}
                        className="animate-ping opacity-75"
                      />
                    )}
                    {/* Pin Outer Circle */}
                    <circle
                      r={isSelected ? 9 : 6}
                      fill={isSelected ? "#06b6d4" : "#10b981"}
                      stroke="#020617"
                      strokeWidth={2}
                    />
                    {/* Pin Inner Dot */}
                    <circle r={2.5} fill="#020617" />

                    {/* Price Tag Label above pin */}
                    <text
                      textAnchor="middle"
                      y={-12}
                      style={{
                        fontFamily: "monospace",
                        fontSize: isSelected ? "11px" : "9px",
                        fontWeight: "bold",
                        fill: isSelected ? "#38bdf8" : "#f1f5f9",
                        textShadow: "0 2px 4px rgba(0,0,0,0.9)",
                      }}
                    >
                      ${v.hourly_rate || 0}/hr
                    </text>
                  </g>
                </Marker>
              );
            })}
          </ZoomableGroup>
        </ComposableMap>
      </div>

      {/* Selected Venue Focus Card Overlay */}
      {selectedVenue && (
        <div className="absolute bottom-4 left-4 right-4 md:right-auto md:w-96 z-20 rounded-2xl bg-[#090d16]/95 backdrop-blur-md border border-cyan-500/50 p-4 shadow-2xl space-y-2 animate-in fade-in slide-in-from-bottom-2 duration-200">
          <div className="flex items-start justify-between">
            <div>
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800/80 font-bold">
                {selectedVenue.venue_type}
              </span>
              <h3 className="text-sm font-bold text-white mt-1 leading-snug">{selectedVenue.name}</h3>
              <p className="text-xs text-slate-400 flex items-center space-x-1 mt-0.5">
                <MapPin className="w-3 h-3 text-slate-500 shrink-0" />
                <span className="truncate">{selectedVenue.address || selectedVenue.city}</span>
              </p>
            </div>
            <div className="text-right font-mono">
              <div className="text-xs text-slate-400">RATE</div>
              <div className="text-sm font-bold text-emerald-400">${selectedVenue.hourly_rate || 0}/hr</div>
            </div>
          </div>
          <div className="flex items-center justify-between text-xs font-mono text-slate-300 pt-1 border-t border-slate-800">
            <span>Capacity: {selectedVenue.capacity} Guests</span>
            <span className="text-cyan-400">GPS: {selectedVenue.latitude?.toFixed(2)}, {selectedVenue.longitude?.toFixed(2)}</span>
          </div>
        </div>
      )}
    </div>
  );
}
