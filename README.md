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
npm install
gulp build
python manage.py runserver
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) and log in with the default
user name and password (admin/admin).

## Development

### Fake data

From within the pipenv shell, execute:

```
python manage.py fake
```