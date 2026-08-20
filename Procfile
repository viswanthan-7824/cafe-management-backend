web: python manage.py migrate --noinput && python manage.py seed_demo_data && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
