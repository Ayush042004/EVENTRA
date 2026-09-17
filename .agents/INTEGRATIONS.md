# Integration Boundaries: EVENTRA

All external system interactions must be isolated behind structured adapters in the `integrations/` directory.

---

## Directory Layout & Boundaries

```text
integrations/
├── maps/
│   ├── places.py           # Geocoding, place lookups, venue coordinates
│   └── routing.py          # Driving distance matrix, travel ETA, transit buffers
├── venues/
│   └── discovery.py        # External venue search aggregators or mock provider feeds
├── whatsapp/
│   ├── client.py           # Outbound WhatsApp Business API message dispatcher
│   ├── webhook.py          # Inbound message receiver and signature verification
│   ├── parser.py           # Inbound message intent/status extraction
│   └── templates.py        # Pre-approved WhatsApp message templates
├── notifications/
│   └── push.py             # Web push notifications, VAPID key handling, APNS/FCM
└── llm/
    ├── base.py             # Abstract LLM client interface (invoke, stream, structured)
    ├── provider_a.py       # Primary model implementation (e.g., Anthropic Claude)
    └── provider_b.py       # Fallback model implementation (e.g., Google Gemini / OpenAI)
```

---

## Architectural Isolation Rules

1. **No External API Calls from React Components:**  
   The frontend communicates strictly with backend API routes (`/api/*`). It must NEVER import external SDKs or call third-party endpoints directly.
2. **No External API Calls Directly from Deterministic Engines:**  
   Calculation engines (Dependency, Risk, Schedule, Budget) accept pure in-memory data structures or database entities. They never make network requests.
3. **No External API Calls Directly Scattered Through Agent Nodes:**  
   The Agent reasoning nodes must not make arbitrary ad-hoc HTTP requests. They must invoke strongly-typed tools that delegate to backend services.
4. **Services Call Integration Interfaces:**  
   Domain services (`VenueService`, `NotificationService`, `VendorService`) consume external capabilities strictly via typed abstract interfaces defined in `integrations/`.

---

## Adapter Pattern Example

```text
Frontend (PWA)
     │
     ▼ HTTP POST /api/events/{id}/venue-search
Backend Route (api/routes/venues.py)
     │
     ▼
Domain Service (services/venue_service.py)
     │
     ▼ Calls Abstract Adapter
Integration Adapter (integrations/maps/places.py)
     │
     ▼ Encrypted HTTPS
External Service (Google Maps / Mapbox API)
```

If an external provider changes its API schema or is replaced, only the respective file in `integrations/` is modified. No business logic or agent prompts are touched.
