# Demo Scenarios & Simulation: EVENTRA

Simulations in EVENTRA are not faked UI mockups or pre-scripted animations. They inject authentic incident payloads into the system to demonstrate how the entire engine processes, adapts, and recovers in real time.

---

## Scenario 1: Vendor No-Show (Primary Critical Test)

### Injected Input
- **Event:** Tech Launch Keynote (150 attendees, live in 90 minutes).
- **Incident:** Audio/Visual Provider (`Apex Sound & Lights`) fails to check in 60 minutes prior to keynote. Automated or manual check-in marks vendor status as `NO_SHOW`.

### Expected System Execution Chain
```text
1. DETECT: Incident logged as 'Critical AV Provider No-Show'.
2. INVESTIGATE: Query vendor assignment status, call attempts, and check-in window expiration.
3. IDENTIFY AFFECTED TASKS: 'Stage Mic Setup', 'Audio Check', 'Livestream Broadcast Start'.
4. CALCULATE IMPACT: 3 tasks blocked; critical path delayed by 75 minutes; event start threatened.
5. ASSESS RISK: Priority objective 'Keynote Start at 10:00 AM' is directly breached → Elevate state to EMERGENCY.
6. GENERATE RECOVERY OPTIONS:
   - Option A: Dispatch backup on-call provider 'Volt AV Services' (ETA 25 mins, cost +$350, within budget buffer).
   - Option B: Compress audio check buffer from 30m to 10m using house PA system (quality trade-off).
7. REQUEST APPROVAL: High-impact financial and vendor change routes to Main Organizer's PWA queue.
8. EXECUTE: Organizer taps 'Approve Option A'; system cancels original contract, binds new assignment.
9. VERIFY: Ping backup provider API / receive vendor acceptance webhook; confirm on-site check-in.
10. UPDATED STATE: Re-traverse schedule; clear emergency state; return event to LIVE with updated timeline.
```

---

## Scenario 2: Venue Issue (Spatial Adaptation)

### Injected Input
- **Event:** Outdoor Corporate Gala (300 guests).
- **Incident:** Severe weather alert triggers zone closure or venue flooding 4 hours prior to guest arrival.

### Expected System Execution Chain
```text
1. DETECT: Incident intake logs 'Venue Flooding / Zone Unusable' at primary lawn venue.
2. IDENTIFY AFFECTED SCOPE: Entire event space unusable; all 12 setup tasks blocked.
3. SEARCH ALTERNATIVE VENUES: Call Venue Discovery Service filtering by:
   - Capacity >= 300
   - Facilities: Indoor covered hall, 3-phase power, catering prep zone
   - Max distance: Within 15 miles of current location
   - Availability: Immediate same-day booking
4. EVALUATE FEASIBILITY:
   - Calculate transit ETA and logistics delay for rerouting all suppliers.
   - Run schedule compression to check if setup can complete before evening banquet.
   - Check budget variance against venue cancellation and new deposit fee.
5. GENERATE RECOVERY OPTIONS: Present top viable venue option with trade-off scorecard.
6. APPROVAL: Critical change escalation requiring dual authorization from Main Organizer.
7. VENUE CHANGE & REPLAN: Mutate event venue binding; recalculate all setup start times and vendor transit routes.
8. VERIFY: Confirm venue reservation lock and automated relocation notifications dispatched to all vendors.
```

---

## Scenario 3: Resource Shortage (Procurement & Allocation)

### Injected Input
- **Event:** Design Awards Dinner.
- **Incident:** Supply delivery arrives with 40 missing banquet chairs and 5 missing spotlight fixtures due to transport damage.

### Expected System Execution Chain
```text
1. DETECT: Delivery discrepancy check-in logs missing inventory: `Chairs: -40`, `Spotlights: -5`.
2. CALCULATE SHORTAGE: Required capacity is 160 seated guests; current capacity is 120. Invariant violated.
3. IDENTIFY AFFECTED TASKS: 'Guest Seating Arrangement' and 'Podium Lighting Calibration'.
4. SEARCH AVAILABLE ALTERNATIVES:
   - Query local rental inventory providers in Provider Network.
   - Filter for immediate courier delivery within 45 minutes.
5. CALCULATE FEASIBILITY:
   - Cost: $180 rental + $50 express courier (within pre-authorized $250 manager discretionary cap).
   - Schedule: Delivery completes 30 minutes before doors open.
6. RECOVERY & AUTONOMOUS ACTION:
   - Action impact level evaluated as MINOR (within pre-authorized spending and schedule limits).
   - Autonomous execution dispatches procurement order to 'Rapid Event Rentals'.
7. VERIFY: Courier tracking webhook confirms dispatched status; on-site collaborator marks physical receipt.
8. UPDATED STATE: Resource inventory balanced; tasks unblocked; state reconciled.
```
