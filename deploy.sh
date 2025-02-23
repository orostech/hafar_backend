#!/bin/bash

# Exit immmediately if a command exits with a non-zero status
set -e

# Define variables
PROJECT_DIR=/home/hafar/hafar_backend
VENV_DIR=$PROJECT_DIR/venv

# Navigate to the project directory
cd $PROJECT_DIR || exit

# Pull the latest code from the repository
echo "Pulling latest code..."
git fetch origin
git reset --hard origin/main

# Activate the virtual environment
echo "Activating virtual environment..."
source $VENV_DIR/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Apply database makemigrations
echo "Applying database migrations..."
python manage.py makemigrations

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# # Apply database makemigrations
# echo "Applying database migrations..."
# python manage.py makemigrations

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Restart Daphne or Gunicorn service
echo "Restarting Daphne service..."
sudo systemctl restart daphne

# Restart Nginx
echo "Restarting Nginx..."
sudo systemctl restart nginx

echo "Deployment complete!"

