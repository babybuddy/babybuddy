# Baby Buddy

A buddy for babies to help caregivers to track sleep, feedings, diaper changes,
and tummy time!

## Installation (development)

```
git clone https://github.com/cdubz/babybuddy.git
cd babybuddy
pip install pipenv
pipenv install --dev
pipenv shell
python manage.py migrate
python manage.py createsuperuser
npm install
gulp build
python manage.py collectstatic
python manage.py runserver
```

## Development

### Fake data

From within the pipenv shell, execute:

```
python manage.py fake
```