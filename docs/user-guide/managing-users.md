# Managing Users

## Creating a User

<video style="max-width: 320px;" autoplay controls loop muted playsinline>
  <source src="../../assets/videos/user_add.mp4" type="video/mp4">
</video>

## Changing User Settings

<video style="max-width: 320px;" autoplay controls loop muted playsinline>
  <source src="../../assets/videos/user_settings.mp4" type="video/mp4">
</video>

## Changing User Password

<video style="max-width: 320px;" autoplay controls loop muted playsinline>
  <source src="../../assets/videos/user_password.mp4" type="video/mp4">
</video>

## Caregiver Users

A caregiver is a user intended for a babysitter or other temporary carer. The
role is a Django group, so it grants a set of model permissions and nothing
more.

A caregiver can:

- view children, timers, feedings, diaper changes and sleep entries;
- add and edit feedings, diaper changes, sleep entries and timers, through both
  the web interface and the API;
- open the child dashboard, the timeline and the feeding, sleep and diaper
  change reports.

A caregiver cannot:

- delete any entry;
- see or record medication, temperature, growth (height, weight, BMI, head
  circumference), notes, pumping or tummy time, in lists, on the dashboard, in
  the timeline or in reports;
- manage users, change site settings or reach the database admin area.

!!! warning "The role is not limited to one child"

    A caregiver has access to every child on the instance, and may edit entries
    that other users created. There is no per-child grant, no expiry on the
    access, and Baby Buddy does not record which user created an entry, so a
    caregiver's entries cannot be told apart from anyone else's afterwards.

To withdraw access, clear the **Active** checkbox on the user, or delete the
user. Both take effect immediately, including for an API key that has already
been handed out. Removing only the caregiver group leaves the account able to
sign in as a standard (superuser) user, so deactivate rather than un-tick the
role.

Read only and caregiver are mutually exclusive: a caregiver creates entries,
which is exactly what the read-only role forbids.

## Creating a User from the Command Line

A user's type can be:

- Caregiver (can view the child dashboard and add/edit feedings, diaper
  changes, sleep entries and timers for every child on the instance. Intended
  for a babysitter or other temporary carer)
- Read only (can access all data but not make new entries)
- Standard (default, can access and make/edit any type of entry)
- Staff (bypasses permissions, can access Database Admin area)

There are 2 ways you can create a user from the command line:

1. Passing user's password as an argument:

```shell
python manage.py createuser --username <username> --password <password>
```

This will create a user with the standard privileges.

2. Interactively setting user's password:

```shell
python manage.py createuser --username <username>
```

You will then be prompted to enter and confirm a password.

- If you want to create a user with read only privileges, pass in the `--read_only` flag:

```shell
python manage.py createuser --username <username> --password <password> --read-only
```

- If you want to create a caregiver (e.g. a babysitter) who can only log
  feedings, diaper changes, sleep and timers, pass in the `--caregiver` flag:

```shell
python manage.py createuser --username <username> --password <password> --caregiver
```

- If you want to create a user with the highest level of permission, you can append the `--is-staff` argument:

```shell
python manage.py createuser --username <username> --is-staff
```

- Another argument you can use with this command is `--email`

```shell
python manage.py createuser --username <username> --email <email>
```

- To get a list of supported commands:

```shell
python manage.py createuser --help
```
