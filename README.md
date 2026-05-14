# SmartPark - Smart Parking Platform

A complete Django-based Smart Parking Platform with real-time license plate detection using OpenCV and EasyOCR, live WebSocket streaming, and a comprehensive admin dashboard.

## Features

- **Real-time License Plate Detection**: Uses OpenCV + EasyOCR to detect and read license plates from webcam feed
- **Live Video Streaming**: WebSocket-based real-time feed streaming to the browser
- **Access Control Engine**: Intelligent decision making based on:
  - Vehicle registration status
  - Ban status
  - Operating hours
  - Parking capacity
  - OCR confidence threshold
- **Admin Dashboard**: Full management interface for:
  - Vehicle registration and ban management
  - Parking configuration (hours, capacity)
  - Access log viewing and filtering
  - CSV export functionality
  - Manual entry/exit processing
- **SQLite Database**: No extra setup required
- **Tailwind CSS**: Modern, responsive UI with CDN-only styling (no build step)
- **Django Channels**: Real-time bidirectional communication with WebSocket

## Tech Stack

- **Backend**: Django 4.2, Python 3.11+
- **Database**: SQLite
- **Realtime**: Django Channels 4.x with InMemoryChannelLayer
- **Frontend**: Tailwind CSS (CDN), Vanilla JavaScript
- **Computer Vision**: OpenCV, EasyOCR, Pillow
- **Server**: Daphne (ASGI)

## Quick Start

### 1. Clone and Setup Environment

```bash
# Navigate to project directory
cd /home/yacine/Documents/Projects/smart-parking

# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env and set:
# - SECRET_KEY (generate a new one, or use default for development)
# - DEBUG=True
# - FALLBACK_MODE=False (set to True if no webcam available)
```

### 3. Initialize Database

```bash
# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser (admin account)
python manage.py createsuperuser

# Seed database with sample data
python manage.py seed_parking
```

### 4. Run Development Server

```bash
# Using Daphne (supports WebSocket)
daphne -b 0.0.0.0 -p 8000 smart_parking.asgi:application

# OR using Django development server (no WebSocket support)
python manage.py runserver
```

### 5. Access the Application

- **Main Dashboard**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin
- **Live Detection**: http://localhost:8000/detection/live/
- **Vehicle Management**: http://localhost:8000/vehicles/
- **Access Logs**: http://localhost:8000/access/logs/
- **Configuration**: http://localhost:8000/access/config/

Default credentials from seed:
- Username: `admin`
- Password: (set during createsuperuser)

## Project Structure

```
smart_parking/
├── manage.py
├── requirements.txt
├── .env.example
├── README.md
│
├── smart_parking/           # Main Django project
│   ├── settings.py          # Django configuration
│   ├── urls.py              # URL routing
│   ├── asgi.py              # ASGI configuration (Channels)
│   ├── wsgi.py              # WSGI configuration
│
├── core/                    # Dashboard app
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── api.py              # API endpoints
│   ├── management/commands/seed_parking.py
│   └── templates/core/     # Base, dashboard, login templates
│
├── vehicles/               # Vehicle management app
│   ├── models.py           # Vehicle model
│   ├── forms.py            # Vehicle forms
│   ├── views.py            # Vehicle views
│   ├── urls.py
│   ├── admin.py            # Admin registration
│   └── templates/vehicles/ # Vehicle CRUD templates
│
├── access/                 # Access control app
│   ├── models.py           # AccessLog, ParkingConfig models
│   ├── forms.py            # Config forms
│   ├── views.py            # Access log views
│   ├── logic.py            # Access decision engine
│   ├── urls.py
│   ├── admin.py
│   └── templates/access/   # Logs, config templates
│
├── detection/              # License plate detection app
│   ├── camera.py           # OpenCV + EasyOCR detector
│   ├── consumers.py        # WebSocket consumer
│   ├── routing.py          # WebSocket URL routing
│   ├── views.py            # Detection views
│   ├── urls.py
│   └── templates/detection/ # Live view template
│
└── static/                 # Static files (empty, Tailwind via CDN)
```

## Usage

### Adding a Vehicle

1. Go to **Vehicles** → **Add Vehicle**
2. Enter vehicle details (plate number, owner info, type, brand, color)
3. Set registration status
4. Save

### Managing Access

1. Go to **Access Logs** to view all detection events
2. Filter by date range, event type, plate number, denial reason
3. Export logs as CSV

### Configuration

1. Go to **Configuration**
2. Set operating hours (open/close times)
3. Set maximum parking capacity
4. Use manual override to force OPEN/CLOSED/AUTO mode
5. Monitor current occupancy

### Live Detection

1. Go to **Live Detection**
2. Click "Start Camera" to begin streaming
3. Adjust confidence threshold slider (0.5 - 0.95)
4. Use "Capture Frame" to manually process current frame
5. View detection results in real-time

### Banning a Vehicle

1. Go to **Vehicles** → **[Vehicle]**
2. Click "Ban" button
3. Enter reason for ban
4. Vehicle will be automatically denied entry

## API Endpoints

- `GET /api/status/` - Returns current parking status (JSON)
  - Response: `{status, count, capacity, occupancy, is_full}`

## Camera Fallback Mode

If no webcam is available:

1. Set `FALLBACK_MODE=True` in `.env`
2. Place test images in `media/test_frames/` directory
3. Images will cycle through in the detection stream

## Models

### Vehicle
- Plate number (unique)
- Owner info (name, phone, email)
- Vehicle details (type, brand, color)
- Photo (optional)
- Registration and ban status
- Timestamps

### AccessLog
- Vehicle reference
- Detected plate string
- Event type (ENTRY, EXIT, DENIED)
- Denial reason (if denied)
- OCR confidence score
- Snapshot image
- Timestamp and gate

### ParkingConfig
- Operating hours (open/close time)
- Max capacity
- Current count
- Manual override flags
- Updated by tracking

## Features in Detail

### Access Decision Engine (logic.py)

The decision engine checks vehicles in this order:

1. **Confidence Check**: OCR confidence < 70% → DENIED (LOW_CONFIDENCE)
2. **Config Check**: Parking manually closed → DENIED (MANUAL_CLOSED)
3. **Hours Check**: Outside hours and not manually open → DENIED (OUTSIDE_HOURS)
4. **Registration Check**: Vehicle not found in database → DENIED (NOT_REGISTERED)
5. **Ban Check**: Vehicle is banned → DENIED (BANNED)
6. **Capacity Check**: Parking is full → DENIED (PARKING_FULL)
7. **All Checks Passed** → GRANTED (ENTRY)

### License Plate Detection Pipeline

1. **Preprocessing**: Convert to grayscale, Gaussian blur, Canny edge detection
2. **Candidate Detection**: Find contours matching plate-like characteristics
3. **OCR**: EasyOCR to read plate text from cropped regions
4. **Validation**: Check against database
5. **Decision**: Run through access logic
6. **Logging**: Record event with snapshot

## Troubleshooting

### WebSocket Connection Failed
- Ensure Daphne is running (not standard Django runserver)
- Check browser console for error messages
- Verify firewall allows WebSocket connections

### No Camera Detected
- Set `FALLBACK_MODE=True` in `.env`
- Add test images to `media/test_frames/`
- Or check camera permissions and device connection

### EasyOCR Download Issues
- First run downloads language models (~100MB)
- Ensure internet connection and disk space
- Models cached in `~/.EasyOCR/model/`

### Database Errors
- Run migrations: `python manage.py migrate`
- Check `.env` DATABASE_URL setting
- Delete `db.sqlite3` to start fresh

## Production Deployment

For production deployment:

1. Set `DEBUG=False` in `.env`
2. Generate new `SECRET_KEY`
3. Use PostgreSQL instead of SQLite
4. Configure `ALLOWED_HOSTS`
5. Use Gunicorn + Daphne for ASGI
6. Configure reverse proxy (Nginx)
7. Enable HTTPS/SSL
8. Set up log rotation
9. Configure static files serving

Example Gunicorn command:
```bash
gunicorn -w 4 -b 127.0.0.1:8001 smart_parking.wsgi:application
```

For WebSocket support with Gunicorn, use Daphne:
```bash
daphne -b 0.0.0.0 -p 8000 smart_parking.asgi:application
```

## Development Notes

- All templates use Tailwind CSS via CDN (no build step required)
- Form styling is included in form widgets
- WebSocket automatically reconnects with exponential backoff
- Camera stream runs in background thread
- All database queries are optimized with select_related/prefetch_related

## License

MIT License - Feel free to use this project for any purpose.

## Support

For issues or questions, check the following:
- Django documentation: https://docs.djangoproject.com/
- Channels documentation: https://channels.readthedocs.io/
- OpenCV documentation: https://docs.opencv.org/
- EasyOCR documentation: https://github.com/JaidedAI/EasyOCR
