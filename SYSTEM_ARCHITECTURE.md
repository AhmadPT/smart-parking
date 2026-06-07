# SmartPark - System Architecture

## Overview
SmartPark is a Django 4.2-based Smart Parking Platform with real-time license plate detection via Gemini AI, WebSocket streaming, subscription/payment tiers, zone-based multi-gate support, and an analytics dashboard.

## Tech Stack
- **Backend**: Django 4.2, Python 3.11+
- **Database**: SQLite
- **Realtime**: Django Channels 4.x (InMemoryChannelLayer), Daphne (ASGI)
- **Frontend**: Tailwind CSS (CDN + `darkMode: 'class'`), Vanilla JS, Font Awesome 6, Chart.js
- **Computer Vision**: OpenCV + Gemini Flash Lite API (via `google-generativeai`)
- **Forms**: django-crispy-forms + crispy-tailwind

## Project Structure (Django Apps)

### `smart_parking/` (Main Project Config)
- `settings.py` - Config: installed apps, channels, DB (SQLite), static/media, login URLs, env-based FALLBACK_MODE
- `urls.py` - Root routing: admin, core, vehicles, access, detection, accounts, API status
- `asgi.py` - ASGI config: HTTP (Django) + WebSocket (Channels AuthMiddlewareStack + URLRouter)

### `core/` (Dashboard App)
- `views.py::dashboard` - Aggregates today's entries/exits/denials, passes to `core/dashboard.html`
- `views.py::analytics` - Hourly/daily traffic, denial breakdown, gate usage via Chart.js; passes JSON labels+data
- `api.py::api_parking_status` - GET /api/status/ returns JSON: status, count, capacity, occupancy, is_full
- `templates/core/base.html` - Shell layout: sidebar nav (Dashboard, Live Detection, Vehicles, Access Logs, Analytics, Gates, Zones, Config, Admin), top bar with live parking status badge, periodic `/api/status/` polling every 5s, **dark mode toggle** (localStorage persistence, Tailwind `dark:` classes)
- `templates/core/dashboard.html` - 4 stat cards (occupancy bar, entries, exits, denials) + live camera placeholder + recent logs list; connects to WebSocket for live updates
- `templates/core/login.html` - Login page with dark mode support
- `templates/core/analytics.html` - Chart.js dashboard: hourly bar chart (entries/exits), daily line chart, denial doughnut, gate polar area

### `vehicles/` (Vehicle Management)
- **Models**:
  - `SubscriptionPlan` - name (choices: free/basic/premium/vip), display_name, price, max_entries_per_day, priority_level, has_unlimited_access, description, is_active
  - `Vehicle` - plate_number (unique), owner info, vehicle_type (car/truck/motorcycle/van), brand, color, is_registered, is_banned, ban_reason, photo, notes, subscription_plan (FK), subscription_expires_at, timestamps. Methods: `is_allowed()`, `is_subscription_active()`, `entries_today()`, `can_enter_today()`
- **Views**: list (paginated 20, filter by q/type/status/plan), detail (with recent access logs), add, edit, delete, toggle-ban (POST JSON)
- **URLs**: `/vehicles/` — list, add, `<pk>/`, `<pk>/edit/`, `<pk>/delete/`, `<pk>/toggle-ban/`
- **Templates**: list.html (table with plan badge + search/filter + pagination + inline ban JS), add.html, edit.html, detail.html

### `access/` (Access Control & Logging)
- **Models**:
  - `ParkingConfig` - Singleton: open_time, close_time, max_capacity, current_count, is_manual_open/closed, updated_by
  - `Zone` - name (unique), location, is_active, max_capacity, current_count, timestamps. Methods: `is_full()`, `occupancy_pct()`, `gates_list()`
  - `Gate` - zone (FK), name, direction (ENTRANCE/EXIT), camera_ip, camera_port, camera_username, camera_password, is_active, open_time, close_time, allowed_vehicle_types, timestamps. unique_together(zone, name). Methods: `is_within_hours()`, `allows_vehicle_type()`, `rtsp_url()`
  - `AccessLog` - vehicle (FK), plate_detected, event_type (ENTRY/EXIT/DENIED), denial_reason, confidence_score, snapshot image, timestamp, gate, zone (FK nullable), processed_by
- **Logic** (`logic.py`):
  - `clean_plate()` - Normalizes plate string (uppercase, strip non-alphanumeric)
  - `save_snapshot()` - numpy array → PIL → ContentFile
  - `process_detection()` - Decision engine: confidence → manual closed → gate hours → registered → banned → subscription active → daily limit → **zone capacity** → vehicle type allowed → GRANTED. Increments zone.current_count via `F()`.
  - `process_exit()` - Finds ENTRY without EXIT, decrements zone.current_count via `F()` update.
- **Views**: logs (paginated 30, filter by date/event/plate/reason), export CSV, config (edit hours/capacity), toggle_override, reset_count, Zone CRUD (list/add/edit/delete), Gate CRUD (list/add/edit/delete)
- **URLs**: `/access/logs/`, `/access/export/`, `/access/config/`, `/access/toggle-override/`, `/access/reset-count/`, `/access/zones/`, `/access/zones/add/`, `/access/zones/<pk>/edit/`, `/access/zones/<pk>/delete/`, `/access/gates/`, `/access/gates/add/`, `/access/gates/<pk>/edit/`, `/access/gates/<pk>/delete/`
- **Templates**: logs.html (filter form + stats + table + pagination), config.html (hours form + status + manual override buttons), zones.html, zone_form.html, gates.html (zone/direction/camera IP columns), gate_form.html

### `detection/` (License Plate Detection)
- **`camera.py`**:
  - `LicensePlateDetector` singleton class
  - Initializes Gemini model via `google-generativeai` (requires `GEMINI_API_KEY` env var)
  - `preprocess_frame()` - Grayscale + CLAHE
  - `read_plate_with_gemini()` - Sends frame to Gemini Flash Lite for OCR, returns plate text + confidence
  - `process_frame(frame, use_ai=False)` - Only queries Gemini when `use_ai=True` (manual trigger); otherwise reuses last result. Annotates HUD on frame.
  - `capture_loop()` - Background thread: cycles fallback frames (if FALLBACK_MODE) or reads RTSP/webcam
  - `start_stream()` - Looks up active Gate by `current_gate`, connects to RTSP URL (if camera_ip set) or falls back to webcam index 0
  - `stop_stream()` - Thread lifecycle
  - `encode_frame()` - Frame → base64 JPEG
- **`consumers.py`**:
  - `ParkingConsumer` (AsyncWebsocketConsumer) - WebSocket at `/ws/detection/`
  - `connect()` - Accepts, joins 'parking_feed' group, spawns frame sender task
  - `receive()` - Handles 'start', 'stop', 'manual_trigger' actions with gate parameter
  - `send_frames_periodically()` - Every 0.1s sends encoded frame + detection result + config/zone status
  - `_get_config(gate_name)` - Resolves gate → zone for capacity display; falls back to ParkingConfig
- **URLs**: `/detection/live/`, `/detection/manual-trigger/` (POST)
- **Templates**: live.html — canvas for video, camera controls (start/stop/capture), **dynamic gate dropdown** from DB, confidence slider, detection result panel, snapshot gallery placeholder

## Data Flow

### Detection Pipeline
1. Camera (RTSP from Gate camera_ip / webcam / fallback image) → `capture_loop()` → `process_frame(use_ai=False)` (no AI, reuses last result)
2. User clicks "Capture Frame" → JS freezes canvas, sends base64 frame via WebSocket `manual_trigger`
3. Backend decodes frame → `process_frame(use_ai=True)` → `read_plate_with_gemini()` → `process_detection()`
4. Result sent back via WebSocket `manual_result` → JS updates UI and shows "Back to Live" button
5. Periodic frames (0.1s) sent via WebSocket `frame_stream` → JS draws on canvas

### Access Decision Flow (`process_detection`)
plate_string + confidence → clean_plate → check confidence ≥70% → check manual closed → check gate hours → lookup Vehicle → check banned → check registered → check subscription active → check daily limit → check **zone capacity** (zone.is_full()) → check vehicle type → GRANTED (entry, increment zone count) / DENIED (with reason)

### Subscription Check Flow
Vehicle → subscription_plan FK → plan.max_entries_per_day (0=unlimited) → entries_today() < max → DENIED/GRANTED

### WebSocket Message Types
- **Server → Client**: `frame_stream` (live frames + detection data + zone capacity), `frame_update`
- **Client → Server**: `start`, `stop`, `manual_trigger` (with base64 frame + gate name)
- **Server → Client (response)**: `manual_result` (plate, decision, reason, confidence, vehicle_name, gate)

## Key Files Reference
| File | Purpose |
|------|---------|
| `smart_parking/settings.py` | Django config, installed apps, channels, DB |
| `smart_parking/asgi.py` | ASGI app with WebSocket routing |
| `smart_parking/urls.py` | Root URL configuration |
| `core/views.py` | Dashboard + Analytics views |
| `core/api.py` | JSON status API endpoint |
| `vehicles/models.py` | SubscriptionPlan + Vehicle models |
| `vehicles/views.py` | Vehicle CRUD + ban toggle |
| `access/models.py` | Zone + Gate + ParkingConfig + AccessLog models |
| `access/logic.py` | Access decision engine (process_detection, process_exit) |
| `access/views.py` | Logs, config, override, reset, CSV export, Zone/Gate CRUD |
| `detection/camera.py` | LicensePlateDetector class (Gemini AI, OpenCV, RTSP capture loop) |
| `detection/consumers.py` | WebSocket consumer (ParkingConsumer, zone-aware config) |
| `detection/routing.py` | WebSocket URL patterns |
| `core/templates/core/base.html` | Base layout with dark mode toggle |
| `core/templates/core/analytics.html` | Chart.js traffic analytics dashboard |

## Environment Variables (.env)
- `SECRET_KEY` - Django secret
- `DEBUG` - Boolean
- `ALLOWED_HOSTS` - Comma-separated
- `FALLBACK_MODE` - Use test images instead of webcam/RTSP
- `GEMINI_API_KEY` - Google Gemini API key for OCR
- `WEBHOOK_SECRET` - (unused in current code)
