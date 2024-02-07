# HTTPS/SSL

The example Docker and manual deployment methods do not include HTTPS/SSL by default.
Additional tools and configuration are required to add HTTPS support.

## Configuration requirements

For either approach (host- or container-based) Baby Buddy's configuration will need to
be updated to account for the proxy. For details on these settings see [Proxy configuration](proxy.md).

After configuring the proxy set the following two environment variables and then restart
necessary services:

```ini
CSRF_TRUSTED_ORIGINS=https://babybuddy.example.com
SECURE_PROXY_SSL_HEADER=True
```

## Host-based proxy

This guide assumes Baby Buddy has been deployed to a Debian-like system with
[snapd installed](https://snapcraft.io/docs/installing-snapd) using the [example deployment](deployment.md#example-deployment)
however this approach can also be used with a Docker deployment if having the proxy
in the host is desired (otherwise see [Container-based proxy](#container-based-proxy)).

If the example deployment with uWSGI and NGINX is already used skip to [Install Certbot](#install-certbot)
and [Obtain and install certificate](#obtain-and-install-certificate).

### Install NGINX

If NGINX is not already installed on the host system install it with a package manager.

```shell
apt-get -y install nginx
```

NGINX will be used to proxy HTTPS traffic to Baby Buddy. There are many other proxies
available for this (often with Let's Encrypt support, as well) so a different one can
be used if desired.

#### Configure NGINX

If Baby Buddy is running from Docker a new NGINX site will need to be created to send
traffic to Docker. The configuration below uses the example domain `babybuddy.example.com`
and assumes Docker has exposed Baby Buddy on port `8000` (the default configuration).

```shell
editor /etc/nginx/sites-available/babybuddy
```

Initial configuration:

```nginx
server_tokens               off;
access_log                  /var/log/nginx/babybuddy.access.log;
error_log                   /var/log/nginx/babybuddy.error.log;

server {
  server_name               babybuddy.example.com;
  location / {
    proxy_pass              http://localhost:8000;
    proxy_set_header        Host $host;
  }
}
```

Enable the new site:

```shell
ln -s /etc/nginx/sites-available/babybuddy /etc/nginx/sites-enabled/babybuddy
service nginx restart
```

Confirm the site is not accessible at `http://babybuddy.example.com`. Note: Attempting
to log in will result in a CSRF error! This will be addressed after HTTPS has been
established.

### Install Certbot

This example uses [Let's Encrypt's](https://letsencrypt.org/) free service for obtaining
SSL certificates. Other methods can be used to obtain and install a certificate as
desired.

[Certbot](https://certbot.eff.org/instructions) is used to obtain free SSL certificates
from Let's Encrypt.

```shell
snap install core && snap refresh core
snap install --classic certbot
ln -s /snap/bin/certbot /usr/bin/certbot
```

### Obtain and install certificate

The following command will ask for an email address to register with Let's Encrypt and
then prompt a service agreement and which NGINX host to obtain a certificate for. The
certificate will be installed and activated automatically.

```shell
certbot --nginx
[answers prompts as required]
service nginx restart
```

Certbot should have updated the NGINX site configuration (`/etc/nginx/sites-available/babybuddy`)
to look something like this:

```nginx
server_tokens               off;
access_log                  /var/log/nginx/babybuddy.access.log;
error_log                   /var/log/nginx/babybuddy.error.log;

server {
  server_name               babybuddy.example.com;
  location / {
    proxy_pass              http://localhost:8000;
    proxy_set_header        Host $host;
  }

    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/babybuddy.example.com/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/babybuddy.example.com/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot
}

server {
    if ($host = babybuddy.example.com) {
        return 301 https://$host$request_uri;
    } # managed by Certbot

  server_name               babybuddy.example.com;
  listen                    80;
    return 404; # managed by Certbot
}
```

If the certificate was obtained by some other means the configuration about should be
instructive for how to add it to the NGINX site configuration.

## Container-based proxy

If Baby Buddy is already hosted in a Docker container the proxy (NGINX) can be hosted
there as well. The configuration provided here assumes the `docker-compose.yml` example
from the [Docker deployment method](deployment.md#docker) is used.

### Add NGINX service

Add the following `services` entry to `docker-compose.yml`:

```yaml
babybuddy-nginx:
  image: nginx
  container_name: babybuddy-nginx
  volumes:
    - /path/to/appdata/nginx.conf:/etc/nginx/conf.d/default.conf
    - /path/to/appdata/logs:/var/log/nginx
    - /path/to/appdata/certs:/certs
  ports:
    - 80:80
    - 443:443
  depends_on:
    - babybuddy
```

Set the contents of `/path/to/appdata/nginx.conf` to:

```nginx
server {
    server_name         babybuddy.example.com;
    listen              443 ssl;
    ssl_certificate     /certs/babybuddy.example.com.crt;
    ssl_certificate_key /certs/babybuddy.example.com.key;
    location / {
        proxy_pass              http://babybuddy:8000;
        proxy_set_header        Host $host;
    }
}

server {
    if ($host = babybuddy.example.com) {
        return 301 https://$host$request_uri;
    }

    server_name         babybuddy.example.com;
    listen              80;
    return 404;
}
```

### Add certificates

Place certificates in `/path/to/appdata/certs` using the files name of `ssl_certificate`
and `ssl_ceritifcate_key` in the NGINX configuration.
