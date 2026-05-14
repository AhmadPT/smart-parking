# 📦 Installation & Deployment Guide

## System Requirements

- Python 3.11+
- pip (Python package manager)
- Webcam (optional, fallback mode available)
- Linux/Mac/Windows

## Step-by-Step Installation

### Step 1: Clone or Navigate to Project

```bash
cd /home/yacine/Documents/Projects/smart-parking
```

### Step 2: Create Virtual Environment

```bash
# Linux/Mac
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This will install:
- Django 4.2
- Django Channels 4.x
- Daphne 4.0+
- OpenCV
- EasyOCR
- Pillow
- python-environ
- whitenoise
- crispy-forms

### Step 4: Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env file with your settings:
# SECRET_KEY=your-secret-key (or leave default for dev)
# DEBUG=True (for development)
# FALLBACK_MODE=False (set True if no webcam)
```

### Step 5: Initialize Database

```bash
# Create tables
python manage.py migrate

# Create superuser (admin account)
python manage.py createsuperuser

# Seed database with sample data
python manage.py seed_parking
```

### Step 6: Collect Static Files (Optional for development)

```bash
python manage.py collectstatic --noinput
```

### Step 7: Run the Server

```bash
# Using Daphne (recommended - supports WebSocket)
daphne -b 0.0.0.0 -p 8000 smart_parking.asgi:application

# OR using Django development server (no WebSocket)
python manage.py runserver
```

### Step 8: Access the Application

Open your browser and navigate to:

- **Main Dashboard**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin
- **Live Detection**: http://localhost:8000/detection/live/
- **Vehicles**: http://localhost:8000/vehicles/
- **Access Logs**: http://localhost:8000/access/logs/
- **Configuration**: http://localhost:8000/access/config/

---

## Docker Installation (Optional)

### Using Docker Compose

```bash
# Navigate to project directory
cd /home/yacine/Documents/Projects/smart-parking

# Build and run
docker-compose up

# Access at http://localhost:8000
```

The Docker setup will:
- ✅ Install all dependencies
- ✅ Run migrations automatically
- ✅ Seed database with sample data
- ✅ Start Daphne server on port 8000

---

## Production Deployment

### Prerequisites

- Server with Python 3.11+ installed
- PostgreSQL database (recommended over SQLite)
- Domain name with SSL certificate
- Gunicorn or similar WSGI server
- Reverse proxy (Nginx recommended)

### Production Setup

1. **Install System Dependencies**
   ```bash
   sudo apt-get update
   sudo apt-get install python3.11 python3-pip postgresql nginx
   ```

2. **Create Application User**
   ```bash
   sudo useradd -m smart-parking
   sudo su - smart-parking
   ```

3. **Clone Repository**
   ```bash
   git clone <repository-url> smart-parking
   cd smart-parking
   ```

4. **Setup Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

5. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

6. **Configure Environment for Production**
   ```bash
   cp .env.example .env
   nano .env
   ```
   
   Required settings:
   ```
   SECRET_KEY=<generate-secure-key>
   DEBUG=False
   ALLOWED_HOSTS=your-domain.com,www.your-domain.com
   DATABASE_URL=postgresql://user:password@localhost:5432/smartpark
   SECURE_SSL_REDIRECT=True
   SESSION_COOKIE_SECURE=True
   CSRF_COOKIE_SECURE=True
   ```

7. **Create PostgreSQL Database**
   ```bash
   sudo -u postgres psql
   CREATE DATABASE smartpark;
   CREATE USER smartpark WITH PASSWORD 'secure-password';
   ALTER ROLE smartpark SET client_encoding TO 'utf8';
   ALTER ROLE smartpark SET default_transaction_isolation TO 'read committed';
   ALTER ROLE smartpark SET default_transaction_deferrable TO on;
   ALTER ROLE smartpark SET timezone TO 'UTC';
   GRANT ALL PRIVILEGES ON DATABASE smartpark TO smartpark;
   \q
   ```

8. **Run Migrations**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py seed_parking
   ```

9. **Collect Static Files**
   ```bash
   python manage.py collectstatic --noinput
   ```

10. **Create Gunicorn Service File**
    ```bash
    sudo nano /etc/systemd/system/smartpark.service
    ```
    
    Content:
    ```ini
    [Unit]
    Description=SmartPark Django Application
    After=network.target
    
    [Service]
    Type=notify
    User=smart-parking
    WorkingDirectory=/home/smart-parking/smart-parking
    ExecStart=/home/smart-parking/smart-parking/venv/bin/gunicorn \
        --workers 4 \
        --bind unix:/tmp/smartpark.sock \
        smart_parking.wsgi:application
    
    [Install]
    WantedBy=multi-user.target
    ```

11. **Create Daphne Service for WebSocket**
    ```bash
    sudo nano /etc/systemd/system/smartpark-daphne.service
    ```
    
    Content:
    ```ini
    [Unit]
    Description=SmartPark Daphne WebSocket Server
    After=network.target
    
    [Service]
    Type=simple
    User=smart-parking
    WorkingDirectory=/home/smart-parking/smart-parking
    ExecStart=/home/smart-parking/smart-parking/venv/bin/daphne \
        -b 127.0.0.1 \
        -p 8001 \
        --access-log - \
        smart_parking.asgi:application
    Restart=on-failure
    
    [Install]
    WantedBy=multi-user.target
    ```

12. **Configure Nginx**
    ```bash
    sudo nano /etc/nginx/sites-available/smartpark
    ```
    
    Content:
    ```nginx
    upstream smartpark_app {
        server unix:/tmp/smartpark.sock fail_timeout=0;
    }
    
    upstream smartpark_ws {
        server 127.0.0.1:8001;
    }
    
    server {
        listen 443 ssl http2;
        server_name your-domain.com;
        
        ssl_certificate /path/to/cert.pem;
        ssl_certificate_key /path/to/key.pem;
        
        client_max_body_size 10M;
        
        location / {
            proxy_pass http://smartpark_app\;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        location /ws/ {
            proxy_pass http://smartpark_ws\;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
        
        location /static/ {
            alias /home/smart-parking/smart-parking/staticfiles/;
            expires 30d;
        }
        
        location /media/ {
            alias /home/smart-parking/smart-parking/media/;
            expires 7d;
        }
    }
    
    server {
        listen 80;
        server_name your-domain.com;
        return 301 https://$server_name$request_uri\;
    }
    ```

13. **Enable and Start Services**
    ```bash
    sudo systemctl enable smartpark.service smartpark-daphne.service
    sudo systemctl start smartpark.service smartpark-daphne.service
    sudo systemctl restart nginx
    ```

14. **Setup Log Rotation**
    ```bash
    sudo nano /etc/logrotate.d/smartpark
    ```
    
    Content:
    ```
    /home/smart-parking/smart-parking/logs/*.log {
        daily
        rotate 7
        compress
        delaycompress
        notifempty
        create 0640 smart-parking smart-parking
        sharedscripts
    }
    ```

15. **Monitor Application**
    ```bash
    # View logs
    sudo journalctl -u smartpark.service -f
    sudo journalctl -u smartpark-daphne.service -f
    
    # Check service status
    sudo systemctl status smartpark.service
    sudo systemctl status smartpark-daphne.service
    ```

---

## Troubleshooting

### Issue: ModuleNotFoundError
**Solution**: Ensure virtual environment is activated
```bash
source venv/bin/activate
```

### Issue: Port 8000 Already in Use
**Solution**: Use different port or kill process
```bash
# Find process using port 8000
lsof -i :8000
# Kill it
kill -9 <PID>
# Or use different port
daphne -b 0.0.0.0 -p 8001 smart_parking.asgi:application
```

### Issue: Database Connection Error
**Solution**: Check DATABASE_URL in .env and ensure database exists
```bash
# For SQLite (should work automatically)
# For PostgreSQL, ensure postgres service is running
sudo systemctl start postgresql
```

### Issue: Static Files Not Found
**Solution**: Run collectstatic
```bash
python manage.py collectstatic --noinput
```

### Issue: WebSocket Connection Failed
**Solution**: Ensure Daphne is running
- Development: Use `daphne` command
- Production: Ensure daphne service is running and reverse proxy is configured

### Issue: No Camera Detected
**Solution**: Use fallback mode
```
FALLBACK_MODE=True
```
Then place test images in `media/test_frames/`

---

## Environment Variables Reference

```env
# Security
SECRET_KEY=your-secret-key-here
DEBUG=False              # Always False in production

# Server
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
DATABASE_URL=sqlite:///db.sqlite3

# Application
FALLBACK_MODE=False      # Set True if no webcam available
WEBHOOK_SECRET=          # For future webhook integration

# SSL (Production)
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

---

## Backup and Recovery

### Database Backup (SQLite)
```bash
cp db.sqlite3 db.sqlite3.backup
```

### Database Backup (PostgreSQL)
```bash
pg_dump smartpark > smartpark_backup.sql
```

### Restore Database
```bash
psql smartpark < smartpark_backup.sql
```

### Backup Media Files
```bash
tar -czf media_backup.tar.gz media/
```

---

## Performance Optimization

### Enable Caching
Update settings.py:
```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'smartpark-cache',
    }
}
```

### Database Optimization
```bash
# For PostgreSQL, run ANALYZE
psql smartpark -c "ANALYZE;"
```

### Static Files Compression
```bash
# Already handled by WhiteNoiseMiddleware
python manage.py collectstatic --noinput
```

---

## Security Hardening

- ✅ Use strong SECRET_KEY (50+ characters)
- ✅ Enable HTTPS/SSL
- ✅ Set DEBUG=False in production
- ✅ Use PostgreSQL instead of SQLite
- ✅ Implement rate limiting (add django-ratelimit)
- ✅ Regular security updates: `pip install --upgrade -r requirements.txt`
- ✅ Monitor logs for suspicious activity
- ✅ Regular database backups
- ✅ Implement two-factor authentication (optional)

---

**Installation complete! Your Smart Parking Platform is ready to use.** 🎉
