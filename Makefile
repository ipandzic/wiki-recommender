migrations:
	cd recommender && python manage.py makemigrations

migrate:
	cd recommender && python manage.py migrate

showmigrations:
	cd recommender && python manage.py showmigrations $(app)

run:
	cd recommender && python manage.py runserver 8000

superuser:
	cd recommender && python manage.py createsuperuser

shell:
	cd recommender && python manage.py shell
