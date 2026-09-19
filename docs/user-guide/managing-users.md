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

With the default group permissions, a caregiver can:

- view children, timers, feedings, diaper changes, sleep entries, medication,
  temperature, weight, notes and tummy time;
- add and edit feedings, diaper changes, sleep entries, timers, medication,
  temperature, weight, notes and tummy time, through both the web interface and
  the API;
- open the child dashboard, the timeline and the reports for those entry types.

With those defaults, a caregiver cannot:

- delete any entry, including a timer;
- see or record pumping, height, BMI or head circumference, in lists, on the
  dashboard, in the timeline or in reports;
- manage children, tags, users, change site settings or reach the database
  admin area.

The group is a starting point, not a fixed role. A caregiver is an ordinary
Django user, so the permissions can be extended per user afterwards — grant the
ones the group does not include, such as pumping or the growth measurements —
from the database admin area at `/admin/`, where Django's built-in permission
picker lives. The granularity is **additive only**: Django has no per-user deny,
so an individual can be given more than the group, not less. Take a permission
away from one caregiver and it either stays granted through the group or has to
be removed for everybody.

Group permission changes apply to all existing members, not just newly created
users. Each migration run adds any missing default permissions back to the
group and retains manually added permissions. Removing a default from the group
is therefore not a lasting restriction: the next `migrate` restores it.
Per-user permissions are the way to extend one caregiver's access without
changing everybody else's defaults.

Converting a timer into a feeding, sleep or tummy-time entry deletes the timer.
That operation requires `core.delete_timer`, even for a timer the caregiver
created. Without it, the caregiver can record the entry using start and end
times instead; the timer remains until someone with deletion permission removes
it. Granting `core.delete_timer` also permits deleting other users' timers, not
just completing the caregiver's own timers.

Tags already attached to an entry remain visible and are preserved when a
caregiver edits the entry without changing its tags. Changing tag assignments
requires `core.change_tag`; creating new tag names additionally requires
`core.add_tag`. These permissions are not included in the caregiver group.

!!! warning "The role is not limited to one child"

    A caregiver has access to every child on the instance, and may edit entries
    that other users created. There is no per-child grant, no expiry on the
    access, and Baby Buddy does not record which user created an entry, so a
    caregiver's entries cannot be told apart from anyone else's afterwards.

To withdraw access, clear the **Active** checkbox on the user, or delete the
user. Subsequent web and API requests are denied, including requests using an
existing API key. Do not simply clear the **Caregiver** checkbox in Baby Buddy's
user form: saving with neither restricted role selected makes the account a
standard (superuser) user. Removing group membership directly in Django's admin
does not itself change the superuser flag, but any other permissions remain.

Read only and caregiver are mutually exclusive: a caregiver creates entries,
which is exactly what the read-only role forbids. Caregiver and **Staff** are
also mutually exclusive in the user form and the `createuser` command, because
staff access opens administrative pages. When converting an existing account,
review its other groups and individual permissions as well. Changing a role
does not remove those additional grants, so switching an extended caregiver to
read only does not necessarily remove all write access.

## Creating a User from the Command Line

A user's type can be:

- Caregiver (can view the child dashboard and add/edit feedings, diaper
  changes, sleep entries, timers, medication, temperature, weight, notes and
  tummy time for every child on the instance. Intended for a babysitter or
  other temporary carer; the default timer and tag restrictions above apply)
- Read only (can access all data but not make new entries)
- Standard (default, can access and make/edit any type of entry)
- Staff (can access user management, site settings and the Database Admin area;
  available actions still depend on the account's permissions)

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

- If you want to create a user with read only privileges, pass in the `--read-only` flag:

```shell
python manage.py createuser --username <username> --password <password> --read-only
```

- To create a caregiver who can log feedings, diaper changes, sleep, timers,
  medication, temperature, weight, notes and tummy time, pass `--caregiver`.
  It cannot be combined with `--read-only` or `--is-staff`:

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
