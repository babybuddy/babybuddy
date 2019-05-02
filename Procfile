release: python manage.py migrate
web: gunicorn babybuddy.wsgi:application --timeout 30 --log-file -