#!/bin/bash

# Step 1: Activate virtual environment
source venv/bin/activate

# Step 2: Install dependencies
pip install -r requirements.txt

# Step 3: Collect static files
python manage.py collectstatic --noinput

# Step 4: Apply database migrations
python manage.py migrate

# Step 5: Start the application (optional)
daphne hafar_backend.asgi:application --bind 0.0.0.0:8000 &