"use client";

import { AppShell } from "../../../components/shell/AppShell";
import { ConversationalIntake } from "../../../features/event-creation/ConversationalIntake";

export default function NewEventPage() {
  return (
    <AppShell>
      <div className="p-4 md:p-8 max-w-6xl mx-auto">
        <ConversationalIntake />
      </div>
    </AppShell>
  );
}
