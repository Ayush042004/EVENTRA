import Link from "next/link";

export default function DashboardPage() {
  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Operations Command Center</h1>
          <p className="text-slate-400">Select or initialize an active event operation.</p>
        </div>
        <Link
          href="/events/new"
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500"
        >
          Initialize New Event
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/60">
          <h3 className="text-lg font-semibold text-white">Live Operations</h3>
          <p className="text-sm text-slate-400 mt-2">Active state monitoring, health metrics, and emergency triggers.</p>
        </div>
        <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/60">
          <h3 className="text-lg font-semibold text-white">Pending Approvals</h3>
          <p className="text-sm text-slate-400 mt-2">Critical path sign-offs and budget variance approvals.</p>
        </div>
        <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/60">
          <h3 className="text-lg font-semibold text-white">Incident Queue</h3>
          <p className="text-sm text-slate-400 mt-2">Reported discrepancies, delay signals, and recovery options.</p>
        </div>
      </div>
    </div>
  );
}
