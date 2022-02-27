# HTTPS/SSL configuration

The example Docker and manual deployment methods do not include HTTPS/SSL by default.
Additional tools and configuration are required to add HTTPS support.

The information here assumes Baby Buddy has been deployed to a Debian-like system with
[snapd installed](https://snapcraft.io/docs/installing-snapd) for Certbot support with
Let's Encrypt. These requirements can skipped if SSL certificates are obtained by some
other way.

## Install NGINX

If NGINX is not already installed on the host system install it with a package manager.

```shell
apt-get -y install nginx
```

NGINX will be used to proxy HTTPS traffic to Baby Buddy. There are many other proxies
available for this (often with Let's Encrypt support, as well) so a different one can
be used if desired.

### Configure NGINX

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

## Install Certbot

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

## Obtain and install certificate

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

## Update Baby Buddy configuration

Lastly Baby Buddy's configuration will need to updated to account for the proxy. For
details on these settings see [Proxy configuration](proxy.md).

Add the following two environment variables via the Docker or uWSGI configuration (if
using the [example deployment](deployment.md#example-deployment)):

```ini
CSRF_TRUSTED_ORIGINS=https://babybuddy.example.com
SECURE_PROXY_SSL_HEADER=True
```

That's it! Restart Docker or uWSGI and Baby Buddy should not be accessible from HTTPS!
