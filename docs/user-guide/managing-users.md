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

## Creating a User from the Command Line

There are 2 ways you can create a user from the command line:

1. Passing user's password as an argument:

```shell
python manage.py createuser --username <username> --password <password>
```

2. Interactively setting user's password:

```shell
python manage.py createuser --username <username>
```

You will then be prompted to enter and confirm a password.

- If you want to make the user a staff, you can append the `--is-staff` argument:

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
