"use client";

import React from "react";
import { VendorResponse } from "@eventra/contracts";
import { Star, MapPin, Phone, Globe, ExternalLink, ShieldCheck, CheckCircle2, Sparkles } from "lucide-react";

interface ProviderCardProps {
  provider: VendorResponse;
  isAssigned?: boolean;
  onAssign?: (provider: VendorResponse) => void;
  assigning?: boolean;
}

export function ProviderCard({ provider, isAssigned, onAssign, assigning }: ProviderCardProps) {
  const isGoogleMaps = provider.source === "GOOGLE_MAPS" || provider.source === "REAL";
  const confidencePercent = provider.classification_confidence
    ? Math.round(provider.classification_confidence * 100)
    : null;

  return (
    <div className="flex flex-col justify-between rounded-xl border border-slate-800 bg-slate-900/80 p-5 shadow-lg backdrop-blur transition-all duration-200 hover:border-slate-700 hover:shadow-cyan-950/20">
      <div className="space-y-3">
        {/* Header Badges & Source */}
        <div className="flex items-center justify-between gap-2">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="inline-flex items-center rounded-md bg-cyan-950/80 px-2.5 py-0.5 text-xs font-semibold text-cyan-400 border border-cyan-800/60">
              {provider.category.replace(/_/g, " ")}
            </span>
            {provider.source && (
              <span className={`inline-flex items-center rounded-md px-2 py-0.5 text-[11px] font-medium border ${
                isGoogleMaps 
                  ? "bg-emerald-950/70 text-emerald-400 border-emerald-800/60" 
                  : "bg-slate-800/80 text-slate-400 border-slate-700/60"
              }`}>
                {provider.source === "GOOGLE_MAPS" ? "Google Maps" : provider.source}
              </span>
            )}
          </div>
          {confidencePercent !== null && (
            <span className="inline-flex items-center gap-1 text-[11px] font-medium text-slate-400 bg-slate-800/60 px-2 py-0.5 rounded border border-slate-700/50">
              <Sparkles className="h-3 w-3 text-amber-400" />
              {confidencePercent}% match
            </span>
          )}
        </div>

        {/* Title & Raw Google Category */}
        <div>
          <h3 className="text-base font-semibold text-slate-100 group-hover:text-cyan-400 transition-colors">
            {provider.name}
          </h3>
          {provider.raw_category && (
            <p className="text-xs text-slate-400 line-clamp-1 italic mt-0.5">
              Google: {provider.raw_category}
            </p>
          )}
        </div>

        {/* Rating & Reviews */}
        <div className="flex items-center gap-3 text-sm text-slate-300">
          {provider.rating ? (
            <div className="flex items-center gap-1 text-amber-400 font-medium">
              <Star className="h-4 w-4 fill-amber-400 text-amber-400" />
              <span>{provider.rating.toFixed(1)}</span>
              {provider.review_count !== undefined && (
                <span className="text-xs text-slate-500 font-normal">
                  ({provider.review_count} reviews)
                </span>
              )}
            </div>
          ) : (
            <span className="text-xs text-slate-500">Unrated</span>
          )}

          {provider.base_cost !== undefined && provider.base_cost !== null && (
            <span className="text-xs text-slate-400 font-mono">
              Est. ~${provider.base_cost.toLocaleString()}
            </span>
          )}
        </div>

        {/* Location & Contact Info */}
        <div className="space-y-1.5 text-xs text-slate-400 pt-1">
          {provider.address ? (
            <div className="flex items-start gap-1.5">
              <MapPin className="h-3.5 w-3.5 text-slate-500 shrink-0 mt-0.5" />
              <span className="line-clamp-1 text-slate-300">{provider.address}</span>
            </div>
          ) : provider.city ? (
            <div className="flex items-center gap-1.5">
              <MapPin className="h-3.5 w-3.5 text-slate-500 shrink-0" />
              <span>{provider.city}</span>
            </div>
          ) : null}

          {provider.contact_phone && (
            <div className="flex items-center gap-1.5">
              <Phone className="h-3.5 w-3.5 text-slate-500 shrink-0" />
              <span className="font-mono text-slate-300">{provider.contact_phone}</span>
            </div>
          )}

          <div className="flex flex-wrap items-center gap-3 pt-0.5">
            {provider.website && (
              <a
                href={provider.website}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 text-cyan-400 hover:text-cyan-300 transition-colors"
              >
                <Globe className="h-3.5 w-3.5" />
                <span>Website</span>
                <ExternalLink className="h-2.5 w-2.5" />
              </a>
            )}
            {provider.maps_url && (
              <a
                href={provider.maps_url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 text-emerald-400 hover:text-emerald-300 transition-colors"
              >
                <MapPin className="h-3.5 w-3.5" />
                <span>View on Maps</span>
                <ExternalLink className="h-2.5 w-2.5" />
              </a>
            )}
          </div>
        </div>

        {/* Detected Capabilities */}
        {provider.capabilities && provider.capabilities.length > 0 && (
          <div className="flex flex-wrap gap-1 pt-1.5">
            {provider.capabilities.slice(0, 3).map((cap, i) => (
              <span
                key={i}
                className="inline-flex items-center gap-1 rounded bg-slate-800/90 px-2 py-0.5 text-[10px] text-slate-300 border border-slate-700/50"
              >
                <ShieldCheck className="h-2.5 w-2.5 text-cyan-400" />
                {cap.replace(/_/g, " ")}
              </span>
            ))}
            {provider.capabilities.length > 3 && (
              <span className="text-[10px] text-slate-500 self-center">
                +{provider.capabilities.length - 3} more
              </span>
            )}
          </div>
        )}
      </div>

      {/* Action Footer */}
      <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between">
        <span className="text-[11px] text-slate-500 font-mono">
          ID: {provider.id.slice(0, 8)}…
        </span>
        {isAssigned ? (
          <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-400 bg-emerald-950/60 px-3 py-1.5 rounded-lg border border-emerald-800/40">
            <CheckCircle2 className="h-3.5 w-3.5" />
            Assigned
          </span>
        ) : onAssign ? (
          <button
            onClick={() => onAssign(provider)}
            disabled={assigning}
            className="inline-flex items-center gap-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:bg-slate-800 disabled:text-slate-500 text-white px-3 py-1.5 text-xs font-semibold shadow transition-all duration-150 active:scale-95"
          >
            {assigning ? "Assigning…" : "Assign Provider"}
          </button>
        ) : null}
      </div>
    </div>
  );
}
