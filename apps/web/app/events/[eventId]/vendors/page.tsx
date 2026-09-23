"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import {
  searchVendors,
  getAssignmentsForEvent,
  createAssignment,
  checkProviderAvailability,
} from "../../../../lib/api/vendors";
import { getProviderMessages, sendProviderMessage } from "../../../../lib/api/integrations";
import { useEvent } from "../../../../hooks/useEvent";
import type {
  VendorResponse,
  VendorAssignmentResponse,
  ProviderAvailabilityResult,
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
} from "lucide-react";

export default function VendorsPage() {
  const params = useParams();
  const eventId = params?.eventId as string;

  const { event } = useEvent(eventId);

  const [vendors, setVendors] = useState<VendorResponse[]>([]);
  const [assignments, setAssignments] = useState<VendorAssignmentResponse[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [categoryFilter, setCategoryFilter] = useState("");
  const [cityFilter, setCityFilter] = useState("");

  // Messaging Modal State
  const [activeMessagingVendor, setActiveMessagingVendor] = useState<VendorResponse | null>(null);
  const [messages, setMessages] = useState<ProviderMessage[]>([]);
  const [newMessage, setNewMessage] = useState("");
  const [sendingMsg, setSendingMsg] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const [vendorRes, assignRes] = await Promise.all([
        searchVendors({
          category: categoryFilter || undefined,
          city: cityFilter || undefined,
        }),
        getAssignmentsForEvent(eventId),
      ]);
      setVendors(vendorRes.items || []);
      setAssignments(assignRes || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [eventId, categoryFilter, cityFilter]);

  const handleAssign = async (vendor: VendorResponse) => {
    try {
      await createAssignment({
        event_id: eventId,
        vendor_id: vendor.id,
        category: vendor.category,
        agreed_cost: vendor.base_cost,
        notes: "Operational assignment confirmed via Control Center",
      });
      await loadData();
    } catch (err: any) {
      alert(`Assignment failed: ${err?.message}`);
    }
  };

  const openMessaging = async (vendor: VendorResponse) => {
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
      await sendProviderMessage(eventId, activeMessagingVendor.id, newMessage);
      setNewMessage("");
      const res = await getProviderMessages(eventId, activeMessagingVendor.id);
      setMessages(res.items || []);
    } catch (err: any) {
      alert(`Failed to send message: ${err?.message}`);
    } finally {
      setSendingMsg(false);
    }
  };

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-blue-950 text-blue-400 border border-blue-800 font-bold">
            PROVIDER NETWORK
          </span>
          <h1 className="text-2xl md:text-3xl font-extrabold text-white mt-1">
            Vendor Directory & Operational Assignments
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Query capability catalogs, bind operational assignments, and conduct audited communications.
          </p>
        </div>
      </div>

      {/* Assigned Vendors for this event */}
      <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/60">
        <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-800">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <h2 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
              Bound Operational Assignments ({assignments.length})
            </h2>
          </div>
          <span className="text-[10px] font-mono text-slate-500">AUTHORITATIVE</span>
        </div>

        {assignments.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {assignments.map((a) => (
              <div
                key={a.id}
                className="p-3.5 rounded-lg bg-slate-950/80 border border-slate-800 flex items-center justify-between"
              >
                <div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-950 text-blue-300 uppercase">
                    {a.category}
                  </span>
                  <div className="text-xs font-bold text-slate-200 mt-1">
                    {a.vendor?.name || `Provider ${a.vendor_id.slice(0, 8)}`}
                  </div>
                  <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                    AGREED COST: ${a.agreed_cost || 0}
                  </div>
                </div>
                <button
                  onClick={() => openMessaging(a.vendor || { id: a.vendor_id, name: "Provider", category: a.category, city: "Active", status: "ACTIVE", created_at: "", updated_at: "" })}
                  className="p-2 rounded bg-slate-800 hover:bg-slate-700 text-blue-400"
                  title="Message Vendor"
                >
                  <MessageSquare className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="py-4 text-center text-xs text-slate-500 font-mono">
            No providers bound yet. Assign relevant vendors below from the directory.
          </div>
        )}
      </div>

      {/* Directory Filter Bar */}
      <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 flex flex-wrap items-center gap-3">
        <div className="flex items-center space-x-2">
          <Filter className="w-4 h-4 text-slate-500" />
          <span className="text-xs font-bold text-slate-300 uppercase">Filters:</span>
        </div>
        <input
          type="text"
          placeholder="Filter by category (e.g. av, catering)..."
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-600"
        />
        <input
          type="text"
          placeholder="Filter by city (e.g. San Francisco)..."
          value={cityFilter}
          onChange={(e) => setCityFilter(e.target.value)}
          className="px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-600"
        />
      </div>

      {/* Vendors Catalog Grid */}
      <div className="space-y-3">
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
          Network Directory ({vendors.length})
        </h3>

        {loading ? (
          <div className="py-16 text-center text-xs text-slate-500 font-mono">
            Querying Provider Network...
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {vendors.map((v) => {
              const isAssigned = assignments.some((a) => a.vendor_id === v.id);
              return (
                <div
                  key={v.id}
                  className="p-5 rounded-xl border border-slate-800 bg-slate-900/60 flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 uppercase tracking-wide">
                        {v.category}
                      </span>
                      <span className="text-[10px] font-mono text-emerald-400 font-semibold">
                        {v.status}
                      </span>
                    </div>

                    <h4 className="text-base font-bold text-white leading-snug">{v.name}</h4>
                    <p className="text-xs text-slate-400 flex items-center space-x-1 mt-1">
                      <MapPin className="w-3.5 h-3.5 text-slate-500" />
                      <span>{v.city}</span>
                    </p>

                    <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs font-mono">
                      <span className="text-slate-500">BASE COST:</span>
                      <span className="font-bold text-emerald-400">${v.base_cost || 0}</span>
                    </div>
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center space-x-2">
                    <button
                      onClick={() => handleAssign(v)}
                      disabled={isAssigned}
                      className={`flex-1 py-1.5 rounded-lg text-xs font-semibold transition ${
                        isAssigned
                          ? "bg-slate-800 text-slate-500 cursor-not-allowed"
                          : "bg-blue-600 hover:bg-blue-500 text-white shadow-md shadow-blue-900/30"
                      }`}
                    >
                      {isAssigned ? "Assigned" : "Assign to Event"}
                    </button>
                    <button
                      onClick={() => openMessaging(v)}
                      className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300"
                      title="Dispatch Message"
                    >
                      <MessageSquare className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Operational Messaging Modal */}
      {activeMessagingVendor && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="max-w-md w-full rounded-xl bg-slate-900 border border-slate-700 shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150 flex flex-col h-[500px]">
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
                    {activeMessagingVendor.category} • {activeMessagingVendor.city}
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
                      {m.direction === "OUTBOUND" ? "DISPATCHED" : "INBOUND"} • {m.timestamp ? new Date(m.timestamp).toLocaleTimeString() : ""}
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
            <form onSubmit={handleSendMessage} className="p-3 border-t border-slate-800 bg-slate-950/80 flex items-center space-x-2">
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
  );
}
