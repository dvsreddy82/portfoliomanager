release: python src/manage.py migrate
web: gunicorn --pythonpath src portfoliomgr.wsgi --log-file -
worker: python src/manage.py run_huey
