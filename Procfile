release: cd mybackend && python manage.py migrate && python manage.py collectstatic --noinput --clear
web: cd mybackend && gunicorn mybackend.wsgi --log-file -
