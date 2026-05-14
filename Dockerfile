FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/db /app/media /app/staticfiles

EXPOSE 8000

CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "smart_parking.asgi:application"]
