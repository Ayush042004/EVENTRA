"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { ProviderSearch } from "@/features/provider-network/ProviderSearch";
import {
  searchVendors,
  getAssignmentsForEvent,
  createAssignment,
} from "../../../../lib/api/vendors";
import { getProviderMessages, sendProviderMessage } from "../../../../lib/api/integrations";
import { useEvent } from "../../../../hooks/useEvent";
import type {
  VendorResponse,
  VendorAssignmentResponse,
  ProviderMessage,
} from "../../../../types/api";
import {
  Users,
  Search,
  Filter,
  DollarSign,
  MapPin,
  MessageSquare,
  CheckCircle2,
  Clock,
  Plus,
  Send,
  X,
  Sparkles,
  Radio,
} from "lucide-react";

export default function EventVendorsPage() {
  const params = useParams();
  const eventId = params?.eventId as string;

  const { event } = useEvent(eventId);

  const [activeTab, setActiveTab] = useState<"discovery" | "assignments">("discovery");
  const [initialProviders, setInitialProviders] = useState<any[]>([]);
  const [assignments, setAssignments] = useState<VendorAssignmentResponse[]>([]);
  const [assignedVendorIds, setAssignedVendorIds] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [successBanner, setSuccessBanner] = useState<string | null>(null);

  // Messaging Modal State
  const [activeMessagingVendor, setActiveMessagingVendor] = useState<{ id: string; name: string; category?: string; city?: string } | null>(null);
  const [messages, setMessages] = useState<ProviderMessage[]>([]);
  const [newMessage, setNewMessage] = useState("");
  const [sendingMsg, setSendingMsg] = useState(false);

  const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

  const loadData = async () => {
    if (!eventId) return;
    try {
      setLoading(true);
      const [vendorsRes, assignRes] = await Promise.all([
        fetch(`${apiBase}/vendors?limit=50`).then((r) => (r.ok ? r.json() : { items: [] })).catch(() => ({ items: [] })),
        getAssignmentsForEvent(eventId).catch(() => []),
      ]);
      setInitialProviders(vendorsRes.items || []);
      setAssignments(assignRes || []);
      setAssignedVendorIds((assignRes || []).map((a: any) => a.vendor_id));
    } catch (err) {
      console.error("Failed to load initial event vendor data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [eventId]);

  const handleAssignProvider = async (provider: any) => {
    try {
      await createAssignment({
        event_id: eventId,
        vendor_id: provider.id,
        category: (provider.category || "other").toLowerCase(),
        agreed_cost: provider.base_cost || 1000.0,
        notes: `Assigned via Provider Network (${provider.name})`,
      });

      setAssignedVendorIds((prev) => [...prev, provider.id]);
      setSuccessBanner(`Successfully assigned "${provider.name}" to the event.`);
      setTimeout(() => setSuccessBanner(null), 5000);
      await loadData();
    } catch (err: any) {
      alert(err.message || "Failed to assign provider.");
    }
  };

  const openMessaging = async (vendor: { id: string; name: string; category?: string; city?: string }) => {
    setActiveMessagingVendor(vendor);
    try {
      const res = await getProviderMessages(eventId, vendor.id);
      setMessages(res.items || []);
    } catch {
      setMessages([]);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeMessagingVendor || !newMessage.trim()) return;

    setSendingMsg(true);
    try {
      const res = await sendProviderMessage(eventId, activeMessagingVendor.id, newMessage);
      setMessages((prev) => [...prev, res]);
      setNewMessage("");
    } catch (err: any) {
      alert(`Dispatch failed: ${err?.message}`);
    } finally {
      setSendingMsg(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#070b12] p-4 md:p-8 text-slate-100 font-sans space-y-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-5">
          <div>
            <div className="flex items-center gap-2.5">
              <span className="rounded-lg bg-cyan-950/80 px-2.5 py-1 text-[11px] font-mono font-semibold text-cyan-400 border border-cyan-800/60">
                PROVIDER NETWORK
              </span>
              {event?.event_type && (
                <span className="rounded-lg bg-slate-800 px-2.5 py-1 text-[11px] font-medium text-slate-300 border border-slate-700">
                  {event.event_type}
                </span>
              )}
            </div>
            <h1 className="text-2xl md:text-3xl font-black text-slate-100 tracking-tight mt-2">
              {event?.name || "Event Provider Network"}
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Search, discover with Google Maps, and manage contracted vendor assignments.
            </p>
          </div>

          {/* Quick Context Pill */}
          {event && (
            <div className="flex flex-wrap items-center gap-4 bg-slate-900/80 border border-slate-800 px-4 py-3 rounded-xl text-xs text-slate-300">
              {event.guest_count > 0 && (
                <div className="flex items-center gap-1.5">
                  <Users className="h-4 w-4 text-cyan-400" />
                  <span>{event.guest_count} Guests</span>
                </div>
              )}
              {event.location && (
                <div className="flex items-center gap-1.5">
                  <MapPin className="h-4 w-4 text-emerald-400" />
                  <span>{event.location}</span>
                </div>
              )}
              <div className="flex items-center gap-1.5">
                <Radio className="h-4 w-4 text-amber-400" />
                <span>{event.state || "ACTIVE"}</span>
              </div>
            </div>
          )}
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center space-x-2 border-b border-slate-800/80 pb-3">
          <button
            onClick={() => setActiveTab("discovery")}
            className={`px-4 py-2 rounded-lg text-xs font-semibold flex items-center space-x-2 transition ${
              activeTab === "discovery"
                ? "bg-blue-600 text-white shadow-md shadow-blue-900/30"
                : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Google Maps Discovery & Network</span>
          </button>
          <button
            onClick={() => setActiveTab("assignments")}
            className={`px-4 py-2 rounded-lg text-xs font-semibold flex items-center space-x-2 transition ${
              activeTab === "assignments"
                ? "bg-blue-600 text-white shadow-md shadow-blue-900/30"
                : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
            }`}
          >
            <Users className="w-3.5 h-3.5" />
            <span>Event Assignments & Messaging ({assignments.length})</span>
          </button>
        </div>

        {/* Assignment Success Notification */}
        {successBanner && (
          <div className="rounded-xl border border-emerald-900/80 bg-emerald-950/60 p-4 text-xs text-emerald-300 flex items-center gap-3">
            <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
            <span>{successBanner}</span>
          </div>
        )}

        {/* Tab 1: Discovery & Google Maps Search */}
        {activeTab === "discovery" && (
          <ProviderSearch
            eventId={eventId}
            initialProviders={initialProviders}
            assignedVendorIds={assignedVendorIds}
            defaultCity={event?.location || "Seattle"}
            onAssignProvider={handleAssignProvider}
          />
        )}

        {/* Tab 2: Assigned Vendors & Messaging */}
        {activeTab === "assignments" && (
          <div className="space-y-6">
            <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-slate-200">Active Contracted Providers</h3>
                  <p className="text-xs text-slate-400">
                    Direct communications dispatch and assignment fulfillment tracking.
                  </p>
                </div>
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                  {assignments.length} assigned
                </span>
              </div>

              {assignments.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pt-2">
                  {assignments.map((a) => (
                    <div
                      key={a.id}
                      className="p-4 rounded-xl border border-slate-800 bg-[#090d16] flex flex-col justify-between space-y-3"
                    >
                      <div className="space-y-1.5">
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-blue-950/80 text-blue-400 border border-blue-800/60">
                            {a.category}
                          </span>
                          <span className="text-[10px] font-mono text-emerald-400">
                            {a.status}
                          </span>
                        </div>
                        <h4 className="text-sm font-bold text-slate-100">
                          {a.vendor?.name || `Vendor #${a.vendor_id}`}
                        </h4>
                        <div className="text-xs font-mono text-slate-400 flex items-center justify-between pt-2 border-t border-slate-800/80">
                          <span>AGREED COST:</span>
                          <span className="font-bold text-emerald-400">${a.agreed_cost || 0}</span>
                        </div>
                      </div>

                      <div className="flex items-center space-x-2 pt-2 border-t border-slate-800/60">
                        <button
                          onClick={() =>
                            openMessaging({
                              id: a.vendor_id,
                              name: a.vendor?.name || a.vendor_id,
                              category: a.category,
                            })
                          }
                          className="w-full py-1.5 rounded-lg bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 border border-blue-500/40 text-xs font-semibold flex items-center justify-center space-x-1.5 transition"
                        >
                          <MessageSquare className="w-3.5 h-3.5" />
                          <span>Dispatch Operational Alert</span>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-12 text-center text-xs text-slate-500 font-mono">
                  No providers bound yet. Switch to the Discovery tab to search and assign vendors.
                </div>
              )}
            </div>
          </div>
        )}

        {/* Operational Messaging Modal */}
        {activeMessagingVendor && (
          <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="max-w-md w-full rounded-xl bg-slate-900 border border-slate-700 shadow-2xl overflow-hidden flex flex-col h-[500px]">
              {/* Modal Header */}
              <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/80">
                <div className="flex items-center space-x-2.5">
                  <div className="p-1.5 rounded-lg bg-blue-950 text-blue-400 border border-blue-800">
                    <MessageSquare className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-slate-100">
                      {activeMessagingVendor.name}
                    </h3>
                    <p className="text-[10px] font-mono text-slate-400 uppercase">
                      {activeMessagingVendor.category || "VENDOR"}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setActiveMessagingVendor(null)}
                  className="text-slate-400 hover:text-slate-200 p-1"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Conversation Messages */}
              <div className="flex-1 p-4 overflow-y-auto space-y-2.5 bg-[#070b12] text-xs">
                {messages.length > 0 ? (
                  messages.map((m, idx) => (
                    <div
                      key={idx}
                      className={`p-2.5 rounded-lg max-w-[85%] ${
                        m.direction === "OUTBOUND"
                          ? "ml-auto bg-blue-600/30 text-blue-100 border border-blue-600/50"
                          : "mr-auto bg-slate-800/80 text-slate-200 border border-slate-700"
                      }`}
                    >
                      <div className="text-[10px] font-mono text-slate-400 mb-0.5">
                        {m.direction === "OUTBOUND" ? "DISPATCHED" : "INBOUND"} •{" "}
                        {m.timestamp ? new Date(m.timestamp).toLocaleTimeString() : ""}
                      </div>
                      <p>{m.message}</p>
                    </div>
                  ))
                ) : (
                  <div className="py-24 text-center text-slate-500 font-mono text-xs">
                    No previous messages. Dispatch an operational alert below.
                  </div>
                )}
              </div>

              {/* Input Form */}
              <form
                onSubmit={handleSendMessage}
                className="p-3 border-t border-slate-800 bg-slate-950/80 flex items-center space-x-2"
              >
                <input
                  type="text"
                  placeholder="Type operational alert or dispatch..."
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  className="flex-1 px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-blue-600"
                />
                <button
                  type="submit"
                  disabled={sendingMsg || !newMessage.trim()}
                  className="p-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white disabled:opacity-50"
                >
                  <Send className="w-4 h-4" />
                </button>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
