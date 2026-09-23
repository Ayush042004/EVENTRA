"use client";

import React, { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import {
  Bell,
  Send,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  MessageSquare,
  Mail,
  Smartphone,
} from "lucide-react";
import { listNotifications, sendNotification } from "../../../../lib/api/integrations";
import type { NotificationItem } from "../../../../types/api";

export default function NotificationsPage() {
  const params = useParams();
  const eventId = params.eventId as string;

  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Send form
  const [title, setTitle] = useState("");
  const [message, setMessage] = useState("");
  const [channel, setChannel] = useState("IN_APP");
  const [recipient, setRecipient] = useState("ALL_LEADS");

  async function loadNotifications() {
    try {
      setLoading(true);
      setError(null);
      const res = await listNotifications(eventId);
      setNotifications(res.items || []);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load notifications";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (eventId) {
      loadNotifications();
    }
  }, [eventId]);

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim() || !message.trim()) return;
    try {
      setSending(true);
      await sendNotification(eventId, {
        notification_type: "OPERATIONAL_BROADCAST",
        title,
        message,
        channel,
        recipient,
      });
      setTitle("");
      setMessage("");
      await loadNotifications();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to dispatch notification";
      alert(msg);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border/40 pb-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
              <Bell className="w-6 h-6 text-primary" />
              Operational Communications & Broadcasts
            </h1>
            <span className="font-mono text-[10px] px-2.5 py-0.5 rounded-full bg-secondary text-muted-foreground border border-border/50">
              Multi-Channel Dispatch
            </span>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            Dispatch urgent stage alerts, SMS/Email broadcasts to crew leads, and incident escalations.
          </p>
        </div>

        <button
          onClick={loadNotifications}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-border/60 hover:bg-card/60 text-muted-foreground hover:text-foreground transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl border border-rose-500/30 bg-rose-500/5 text-rose-300 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Dispatch Form */}
        <div className="lg:col-span-5">
          <form
            onSubmit={handleSend}
            className="p-5 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm space-y-4"
          >
            <div className="flex items-center gap-2">
              <Send className="w-4 h-4 text-primary" />
              <h2 className="text-sm font-semibold text-foreground">
                Dispatch Broadcast Alert
              </h2>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-muted-foreground mb-1">
                  Channel
                </label>
                <select
                  value={channel}
                  onChange={(e) => setChannel(e.target.value)}
                  className="w-full p-2.5 rounded-lg bg-secondary/50 border border-border text-foreground"
                >
                  <option value="IN_APP">In-App Command Pill</option>
                  <option value="SMS">SMS Urgent Push</option>
                  <option value="EMAIL">Email Dispatch</option>
                  <option value="WEBHOOK">External Webhook</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-muted-foreground mb-1">
                  Recipient Group
                </label>
                <select
                  value={recipient}
                  onChange={(e) => setRecipient(e.target.value)}
                  className="w-full p-2.5 rounded-lg bg-secondary/50 border border-border text-foreground"
                >
                  <option value="ALL_LEADS">All Stage & Operations Leads</option>
                  <option value="VENDORS">Active On-Site Vendors</option>
                  <option value="SECURITY">Venue & Safety Crew</option>
                  <option value="DIRECTOR">Operations Director Only</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-muted-foreground mb-1">
                  Subject / Alert Header
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Stage Rehearsal Shifted +15m"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full p-2.5 rounded-lg bg-secondary/50 border border-border text-foreground"
                />
              </div>

              <div>
                <label className="block font-semibold text-muted-foreground mb-1">
                  Broadcast Message
                </label>
                <textarea
                  rows={3}
                  required
                  placeholder="Provide operational directives..."
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  className="w-full p-2.5 rounded-lg bg-secondary/50 border border-border text-foreground"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={sending}
              className="w-full inline-flex items-center justify-center gap-2 px-4 py-2 text-xs font-bold rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground shadow-sm transition-colors"
            >
              <Send className={`w-3.5 h-3.5 ${sending ? "animate-spin" : ""}`} />
              {sending ? "Dispatching..." : "Transmit Broadcast"}
            </button>
          </form>
        </div>

        {/* Notifications Roster */}
        <div className="lg:col-span-7 space-y-3">
          <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            Broadcast Log ({notifications.length})
          </div>

          <div className="rounded-xl border border-border/50 bg-card/30 backdrop-blur-sm overflow-hidden">
            {notifications.length === 0 ? (
              <div className="p-12 text-center text-xs text-muted-foreground space-y-2">
                <Bell className="w-8 h-8 text-muted-foreground/40 mx-auto" />
                <p>No operational notifications transmitted yet.</p>
              </div>
            ) : (
              <div className="divide-y divide-border/30">
                {notifications.map((item) => (
                  <div
                    key={item.id}
                    className="p-4 hover:bg-card/40 transition-colors space-y-1.5"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-secondary text-secondary-foreground border border-border/40">
                          {item.channel}
                        </span>
                        <h3 className="text-xs font-bold text-foreground">
                          {item.title}
                        </h3>
                      </div>
                      <span className="text-[10px] font-mono text-muted-foreground shrink-0">
                        {new Date(item.created_at).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </span>
                    </div>

                    <p className="text-xs text-muted-foreground">{item.message}</p>

                    <div className="flex items-center justify-between text-[10px] text-muted-foreground pt-1">
                      <span>Recipient: {item.recipient || "Broadcast"}</span>
                      <span className="text-emerald-400 font-medium">Status: {item.status}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
