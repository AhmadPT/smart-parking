#!/bin/bash
set -e

echo "🚀 SmartPark Setup Script"
echo "========================"

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env and configure SECRET_KEY and other settings"
else
    echo "✓ .env file already exists"
fi

# Run migrations
echo "🗄️  Running database migrations..."
python manage.py migrate

# Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput --clear

# Seed database
echo "🌱 Seeding database with sample data..."
python manage.py seed_parking

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file if needed"
echo "2. Create a superuser: python manage.py createsuperuser"
echo "3. Run server: daphne -b 0.0.0.0 -p 8000 smart_parking.asgi:application"
echo "4. Access dashboard: http://localhost:8000"
echo ""
