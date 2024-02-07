# Subdirectory

Baby Buddy's default configuration assumes deployment in to the root of a web server.
Some additional configuration is required to install Baby Buddy in a subdirectory of a
server instead (e.g., to `http://www.example.com/babybuddy`).

## Minimum version

Baby Buddy added full support for subdirectory installing in version **1.10.2**. While
it is still possible to do a subdirectory installation in older versions of Baby Buddy
it is not recommended.

## [`SUB_PATH`](../configuration/application.md#sub_path)

Set this environment variable to the subdirectory of the Baby Buddy installation. E.g.,
`SUB_PATH=/babybuddy` if the desired URL is `http://www.example.com/babybuddy`).

## uWSGI + NGINX configuration

When using uWSGI and NGINX (as in the [example deployment](deployment.md#example-deployment))
the following configurations are required.

_Assume the subdirectory `babybuddy` for configuration change examples below but this
can be anything includes multiple subdirectories (e.g., `/my/apps/babybuddy`). Other
paths used in these examples also assume a configuration based on the
[example deployment](deployment.md#example-deployment)._

### uWSGI

In the app configuration replace the `module` declaration with a `mount` declaration and
add the `manage-script-name` declaration and [`SUB_PATH`](../configuration/application.md#sub_path)
environment variable to the `[uwsgi]` configuration block.

```diff
- module = %(project).wsgi:application
+ mount = /babybuddy=%(project).wsgi:application
+ manage-script-name = true
+ env = SUB_PATH=/babybuddy
```

### NGINX

Alter the NGINX `server` configuration to include the desired subdirectory path in the
app (Baby Buddy root) and media `location` declarations _and_ add a new declaration for
the static `location`.

```diff
-    location / {
+    location /babybuddy {
```

```diff
+    location /babybuddy/static {
+        alias /var/www/babybuddy/public/static;
+    }
```

```diff
-    location /media {
+    location /babybuddy/media {
```
