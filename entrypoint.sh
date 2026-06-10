#!/bin/bash
# Exit immediately if a command exits with a non-zero status
set -e

echo "========================================"
echo " Starting Baby Buddy Initialization"
echo "========================================"

# Run database migrations autonomously
echo "--> Applying database migrations..."
python manage.py migrate --noinput

echo "--> Initialization complete. Handing off to web server."
echo "========================================"

# The 'exec' command replaces the shell with the Docker CMD (Gunicorn)
# This ensures Gunicorn runs as PID 1 and receives stop signals properly
exec "$@"