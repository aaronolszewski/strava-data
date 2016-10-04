all: requirements database data createuser runserver

requirements:
	pip install -r requirements.txt

data:
	python get-data.py

database:
	psql -U postgres -tc "select 1 from pg_database where datname = 'warehouse'" | grep -q 1 || (psql -U postgres -c "create database warehouse")
	./manage.py makemigrations
	./manage.py migrate

createuser:
	python manage.py createsuperuser

runserver:
	./manage.py runserver

.PHONY: requirements data database createuser runserver