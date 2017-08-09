all: clean requirements database data createuser runserver

requirements:
	pip install -r requirements.txt

data:
	python data_fetcher.py

database:
	psql -U postgres -tc "select 1 from pg_database where datname = 'warehouse'" | grep -q 1 || (psql -U postgres -c "create database warehouse")
	./manage.py makemigrations
	./manage.py migrate

createuser:
	python manage.py createsuperuser

runserver:
	./manage.py runserver

clean:
	-find . -type f -name "*.pyc" -delete

.PHONY: requirements data database createuser runserver clean
