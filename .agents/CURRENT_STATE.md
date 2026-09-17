# Current Development State: EVENTRA

This is a living status document tracking the active engineering state of EVENTRA.

---

## Overall Status
**STATUS:** PHASE 3 COMPLETE

**CURRENT PHASE:** PHASE 3 — Venue + Provider Network (Completed)

---

## Phase 3 Implementation Details

### 1. Venue Network Implemented
- **Data Models**:
  - `Venue`: `id`, `name`, `address`, `city`, `latitude`, `longitude`, `capacity`, `venue_type`, `contact_email`, `contact_phone`, `hourly_rate`, `amenities` (JSON list), `status`, `created_at`, `updated_at`.
  - `VenueAvailability`: `id`, `venue_id`, `start_datetime`, `end_datetime`, `status` (`AVAILABLE`, `BOOKED`, `BLOCKED`, `MAINTENANCE`), `notes`, `created_at`, `updated_at`.
- **Venue Service**: Deterministic CRUD, multi-criteria filtering, availability conflict checking, and factual suitability checking.
- **REST API Routes**:
  - `GET /api/venues`: Search and filter venues with pagination and stable ordering.
  - `POST /api/venues`: Create venue.
  - `GET /api/venues/{venue_id}`: Retrieve venue by ID.
  - `POST /api/venues/{venue_id}/availability`: Add availability or blackout slot.
  - `GET /api/venues/{venue_id}/availability`: Evaluate venue availability for requested time window.
  - `POST /api/venues/{venue_id}/suitability`: Evaluate factual suitability (guest capacity, amenities, time availability).

### 2. Provider (Vendor) Network Implemented
- **Data Models**:
  - `Vendor`: `id`, `name`, `category`, `city`, `contact_name`, `contact_email`, `contact_phone`, `base_cost`, `service_description`, `status`, `created_at`, `updated_at`.
  - `ProviderAvailability`: `id`, `vendor_id`, `start_datetime`, `end_datetime`, `status` (`AVAILABLE`, `BOOKED`, `BLOCKED`), `notes`, `created_at`, `updated_at`.
  - `VendorAssignment`: `id`, `event_id`, `vendor_id`, `category`, `status` (`REQUESTED`, `CONFIRMED`, `CANCELLED`), `agreed_cost`, `notes`, `created_at`, `updated_at`.
- **Provider Service**: Deterministic CRUD, category filtering, city/cost filtering, availability conflict checking, category validation, and assignment management.
- **REST API Routes**:
  - `GET /api/vendors`: Search providers with pagination and stable ordering.
  - `POST /api/vendors`: Create provider.
  - `GET /api/vendors/{vendor_id}`: Retrieve provider by ID.
  - `POST /api/vendors/{vendor_id}/availability`: Add provider availability slot.
  - `GET /api/vendors/{vendor_id}/availability`: Evaluate provider availability for requested time window.
  - `GET /api/vendors/categories/validate`: Validate provider category compatibility against event domains.
  - `POST /api/vendors/assignments`: Create operational provider assignment for an event.
  - `GET /api/vendors/assignments/event/{event_id}`: List assignments for an event.

### 3. Availability Handling
- Deterministic interval intersection checking: window conflict detected when `req_start < slot.end_datetime and req_end > slot.start_datetime`.
- Controlled status handling: `AVAILABLE`, `BOOKED`, `BLOCKED`, `MAINTENANCE`.
- Inactive venues and providers are strictly reported as unavailable with factual explanatory reason.

### 4. Search and Filtering
- Supported filters: city (case-insensitive), capacity limits (min/max), venue type, status, price ceiling, required amenities (complete subset check), and availability windows.
- Sane pagination (`limit`, `offset`) with deterministic, stable tie-breaking ordering (`ORDER BY name ASC, id ASC`).

### 5. Suitability and Category Validation
- Factual scorecard: returns `capacity_satisfied`, `amenities_satisfied`, `missing_amenities`, `availability_satisfied`, and `is_suitable`. Strictly no subjective AI ranking, scores, or "best" labels.
- Domain intelligence integration:
  - **Wedding**: `catering`, `decoration`, `photography`, `videography`, `music`, `lighting`, `transportation`
  - **College Fest**: `sound`, `lighting`, `stage`, `security`, `catering`, `equipment`, `power`
  - **Conference**: `av`, `catering`, `stage`, `lighting`, `connectivity`, `equipment`, `signage`

### 6. Development and Demo Seed Data
- Curated deterministic seed datasets in `seeds/venues/demo_venues.json` and `seeds/vendors/demo_vendors.json`.
- Automated idempotent seed runner in `seeds/seed_runner.py` for test and local development databases.

### 7. Database Migrations
- Alembic revision `0001_phase3` in `apps/api/alembic/versions/0001_phase3_venue_and_provider_network.py`.
- Generates clean, transactional DDL for PostgreSQL with indexes on foreign keys, categories, cities, capacities, and date ranges.

### 8. Verification Results
- **Migrations**: PASS (Alembic dry-run SQL generated cleanly).
- **Tests**: PASS (30/30 tests passing, covering venues, vendors, assignments, domains, API routes, determinism, and seeds).
- **TypeScript Typecheck**: PASS (`npm run typecheck` across web and contracts).
- **Startup**: PASS (FastAPI application imports, mounts, and registers all 20 routes).

### 9. Known Limitations
- Geospatial distance calculation is currently relational (city / lat-long attributes) without PostGIS spatial indices; external Google Places/Maps integration is deferred to future phases.
- Provider booking and procurement transactions are intentionally omitted in Phase 3 per architectural boundaries.

---

## Next Phase
**NEXT PHASE = PHASE 4 — PLANNING ENGINE**
