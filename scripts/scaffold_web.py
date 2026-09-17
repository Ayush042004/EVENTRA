import os
from pathlib import Path

BASE = Path("apps/web")

ROUTES = [
    "app/events/new/page.tsx",
    "app/events/[eventId]/layout.tsx",
    "app/events/[eventId]/page.tsx",
    "app/events/[eventId]/setup/page.tsx",
    "app/events/[eventId]/venue/page.tsx",
    "app/events/[eventId]/plan/page.tsx",
    "app/events/[eventId]/live/page.tsx",
    "app/events/[eventId]/tasks/page.tsx",
    "app/events/[eventId]/vendors/page.tsx",
    "app/events/[eventId]/schedule/page.tsx",
    "app/events/[eventId]/budget/page.tsx",
    "app/events/[eventId]/incidents/page.tsx",
    "app/events/[eventId]/recovery/page.tsx",
    "app/events/[eventId]/procurement/page.tsx",
    "app/events/[eventId]/approvals/page.tsx",
    "app/events/[eventId]/collaborators/page.tsx",
    "app/events/[eventId]/analytics/page.tsx",
    "app/events/[eventId]/notifications/page.tsx",
    "app/events/[eventId]/activity/page.tsx",
]

COMPONENTS = [
    "components/ui/button.tsx",
    "components/ui/card.tsx",
    "components/ui/badge.tsx",
    "components/ui/dialog.tsx",
    "components/ui/input.tsx",
    "components/ui/tabs.tsx",
    "components/shell/AppShell.tsx",
    "components/shell/DesktopSidebar.tsx",
    "components/shell/MobileBottomNav.tsx",
    "components/shell/MobileHeader.tsx",
    "components/shell/EventSwitcher.tsx",
    "components/event/index.ts",
    "components/venue/VenueSearch.tsx",
    "components/venue/VenueMap.tsx",
    "components/venue/VenueFilters.tsx",
    "components/venue/VenueCard.tsx",
    "components/venue/VenueDetails.tsx",
    "components/venue/VenueAvailability.tsx",
    "components/venue/VenueComparison.tsx",
    "components/venue/VenueSelection.tsx",
    "components/venue/VenueBooking.tsx",
    "components/venue/VenueReplacement.tsx",
    "components/planning/index.ts",
    "components/operations/index.ts",
    "components/incidents/index.ts",
    "components/recovery/index.ts",
    "components/procurement/index.ts",
    "components/collaboration/index.ts",
    "components/analytics/index.ts",
    "components/notifications/index.ts",
]

FEATURES = [
    # event-setup
    "features/event-setup/EventSetupForm.tsx",
    "features/event-setup/RequirementForm.tsx",
    "features/event-setup/ConstraintForm.tsx",
    "features/event-setup/ObjectiveForm.tsx",
    # venue-discovery
    "features/venue-discovery/VenueDiscovery.tsx",
    "features/venue-discovery/VenueSearch.tsx",
    "features/venue-discovery/VenueFilters.tsx",
    "features/venue-discovery/VenueComparison.tsx",
    "features/venue-discovery/VenueSelection.tsx",
    "features/venue-discovery/VenueBooking.tsx",
    "features/venue-discovery/VenueReplacement.tsx",
    # provider-network
    "features/provider-network/ProviderSearch.tsx",
    "features/provider-network/ProviderFilters.tsx",
    "features/provider-network/ProviderCard.tsx",
    "features/provider-network/ProviderDetails.tsx",
    "features/provider-network/ProviderComparison.tsx",
    "features/provider-network/ProviderBooking.tsx",
    "features/provider-network/ProviderAssignment.tsx",
    # event-planning
    "features/event-planning/PlanOverview.tsx",
    "features/event-planning/TaskTree.tsx",
    "features/event-planning/DependencyGraph.tsx",
    "features/event-planning/ResourcePlan.tsx",
    "features/event-planning/ScheduleView.tsx",
    "features/event-planning/BudgetView.tsx",
    # live-operations
    "features/live-operations/LiveCommandCenter.tsx",
    "features/live-operations/EventHealth.tsx",
    "features/live-operations/PlannedVsActual.tsx",
    "features/live-operations/TaskStatusBoard.tsx",
    "features/live-operations/ProviderStatusBoard.tsx",
    "features/live-operations/VenueStatus.tsx",
    "features/live-operations/ResourceStatus.tsx",
    "features/live-operations/ScheduleStatus.tsx",
    "features/live-operations/BudgetStatus.tsx",
    "features/live-operations/LiveTimeline.tsx",
    "features/live-operations/EmergencyBanner.tsx",
    # provider-communication
    "features/provider-communication/CommunicationInbox.tsx",
    "features/provider-communication/MessageComposer.tsx",
    "features/provider-communication/ProviderMessage.tsx",
    "features/provider-communication/StatusUpdate.tsx",
    # incidents
    "features/incidents/IncidentFeed.tsx",
    "features/incidents/IncidentCard.tsx",
    "features/incidents/IncidentDetails.tsx",
    "features/incidents/ImpactGraph.tsx",
    "features/incidents/AffectedTasks.tsx",
    "features/incidents/RiskIndicator.tsx",
    "features/incidents/EmergencyState.tsx",
    "features/incidents/DecisionTrace.tsx",
    # impact
    "features/impact/ImpactSummary.tsx",
    "features/impact/DependencyImpactGraph.tsx",
    "features/impact/AffectedEntities.tsx",
    # risk
    "features/risk/RiskSummary.tsx",
    "features/risk/RiskIndicator.tsx",
    # recovery
    "features/recovery/RecoveryPanel.tsx",
    "features/recovery/RecoveryOptionCard.tsx",
    "features/recovery/RecoveryComparison.tsx",
    "features/recovery/Recommendation.tsx",
    "features/recovery/DecisionExplanation.tsx",
    "features/recovery/ApprovalPrompt.tsx",
    "features/recovery/ActionProgress.tsx",
    "features/recovery/VerificationResult.tsx",
    # approvals
    "features/approvals/ApprovalQueue.tsx",
    "features/approvals/ApprovalCard.tsx",
    "features/approvals/ApprovalHistory.tsx",
    # autonomous-operations
    "features/autonomous-operations/AutonomySettings.tsx",
    "features/autonomous-operations/ActionPolicy.tsx",
    "features/autonomous-operations/SpendingLimits.tsx",
    # procurement
    "features/procurement/ProcurementPanel.tsx",
    "features/procurement/ProcurementItem.tsx",
    "features/procurement/ProcurementRecommendation.tsx",
    "features/procurement/OrderApproval.tsx",
    # notifications
    "features/notifications/NotificationCenter.tsx",
    "features/notifications/NotificationItem.tsx",
    "features/notifications/ActionRequiredCard.tsx",
    # analytics
    "features/analytics/EventPerformance.tsx",
    "features/analytics/BudgetPerformance.tsx",
    "features/analytics/IncidentAnalytics.tsx",
    "features/analytics/RecoveryAnalytics.tsx",
    "features/analytics/SchedulePerformance.tsx",
    "features/analytics/PostEventReport.tsx",
    # audit
    "features/audit/AuditTimeline.tsx",
    "features/audit/StateHistory.tsx",
    # collaboration
    "features/collaboration/CollaboratorList.tsx",
    "features/collaboration/InviteCollaborator.tsx",
    "features/collaboration/RoleSelector.tsx",
    "features/collaboration/PermissionMatrix.tsx",
    "features/collaboration/AccessScope.tsx",
    "features/collaboration/ChangeRequest.tsx",
    "features/collaboration/ApprovalRequest.tsx",
    # verification
    "features/verification/VerificationStatus.tsx",
    "features/verification/VerificationResult.tsx",
]

HOOKS = [
    "hooks/useEvent.ts",
    "hooks/useEventState.ts",
    "hooks/useLiveState.ts",
    "hooks/useIncidents.ts",
    "hooks/useRecovery.ts",
    "hooks/useApprovals.ts",
    "hooks/useNotifications.ts",
    "hooks/useOnlineStatus.ts",
    "hooks/useWebSocket.ts",
]

STORES = [
    "stores/eventStore.ts",
    "stores/liveStore.ts",
    "stores/incidentStore.ts",
    "stores/approvalStore.ts",
    "stores/uiStore.ts",
]

LIB = [
    "lib/api/client.ts",
    "lib/api/events.ts",
    "lib/api/venues.ts",
    "lib/api/vendors.ts",
    "lib/api/planning.ts",
    "lib/api/incidents.ts",
    "lib/api/recovery.ts",
    "lib/api/procurement.ts",
    "lib/api/approvals.ts",
    "lib/api/verification.ts",
    "lib/auth/index.ts",
    "lib/permissions/index.ts",
    "lib/maps/index.ts",
    "lib/notifications/index.ts",
    "lib/websocket/index.ts",
    "lib/offline/queue.ts",
    "lib/offline/sync.ts",
    "lib/offline/storage.ts",
]

TYPES = [
    "types/event.ts",
    "types/venue.ts",
    "types/vendor.ts",
    "types/task.ts",
    "types/incident.ts",
    "types/recovery.ts",
    "types/procurement.ts",
    "types/approval.ts",
    "types/notification.ts",
]

PUBLIC = [
    "public/icons/icon-192.png",
    "public/icons/icon-512.png",
    "public/icons/maskable-512.png",
    "public/screenshots/.gitkeep",
]

ALL_FILES = ROUTES + COMPONENTS + FEATURES + HOOKS + STORES + LIB + TYPES + PUBLIC

def main():
    created = 0
    for rel_path in ALL_FILES:
        target = BASE / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            if target.suffix == ".tsx":
                name = target.stem
                if name == "page":
                    content = "export default function Page() {\n  return null;\n}\n"
                elif name == "layout":
                    content = "export default function Layout({ children }: { children: React.ReactNode }) {\n  return <>{children}</>;\n}\n"
                else:
                    content = f"export function {name}() {{\n  return null;\n}}\n"
                target.write_text(content, encoding="utf-8")
            elif target.suffix == ".ts":
                target.write_text("export {};\n", encoding="utf-8")
            elif target.suffix == ".png":
                target.write_bytes(b"")
            else:
                target.write_text("", encoding="utf-8")
            created += 1
    print(f"Scaffolded {created} files across apps/web.")

if __name__ == "__main__":
    main()
