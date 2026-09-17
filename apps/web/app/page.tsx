import Link from "next/link";

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-6 text-center">
      <div className="max-w-2xl space-y-6">
        <h1 className="text-4xl font-extrabold tracking-tight sm:text-6xl text-white">
          EVENTRA
        </h1>
        <p className="text-xl text-slate-400 font-medium">
          Adaptive Event Operations Platform
        </p>
        <p className="text-sm text-slate-500">
          Plan the event. Run the event. Adapt when reality changes.
        </p>
        <div className="flex gap-4 justify-center pt-4">
          <Link
            href="/dashboard"
            className="rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-500"
          >
            Enter Command Center
          </Link>
          <Link
            href="/events"
            className="rounded-lg border border-slate-700 px-5 py-2.5 text-sm font-semibold text-slate-300 hover:bg-slate-900"
          >
            View Events
          </Link>
        </div>
      </div>
    </main>
  );
}
