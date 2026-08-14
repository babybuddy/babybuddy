# syntax=docker/dockerfile:1
#
# linuxserver/babybuddy-compatible image that installs THIS repository
# instead of curling an upstream release tarball.
#
# Drop-in replacement for lscr.io/linuxserver/babybuddy:
#   - Env: PUID, PGID, TZ, CSRF_TRUSTED_ORIGINS (plus other Baby Buddy env vars)
#   - Volume: /config
#   - Ports: 8000 (and 80/443 from the nginx base image)
#   - Default login: admin / admin
#
# https://docs.linuxserver.io/images/docker-babybuddy/

FROM ghcr.io/linuxserver/baseimage-alpine-nginx:3.24

ARG BUILD_DATE
ARG VERSION
LABEL build_version="Helvio88/babybuddy version:- ${VERSION} Build-date:- ${BUILD_DATE}"
LABEL maintainer="helvio88"

ENV S6_STAGE2_HOOK="/init-hook"

RUN \
  echo "**** install build packages ****" && \
  apk add --no-cache --virtual=build-dependencies \
    build-base \
    jpeg-dev \
    libffi-dev \
    libxml2-dev \
    libxslt-dev \
    mariadb-dev \
    postgresql-dev \
    python3-dev \
    zlib-dev && \
  echo "**** install runtime packages ****" && \
  apk add --no-cache \
    jpeg \
    libffi \
    libpq \
    libxml2 \
    libxslt \
    mariadb-connector-c \
    python3

# Install this repository (not an upstream GitHub release tarball).
COPY . /app/www/public

RUN \
  echo "**** install babybuddy ****" && \
  cd /app/www/public && \
  python3 -m venv /lsiopy && \
  pip install -U --no-cache-dir \
    pip \
    setuptools && \
  pip install -U --no-cache-dir --find-links https://wheel-index.linuxserver.io/alpine-3.24/ \
    -r requirements.txt && \
  pip install -U --no-cache-dir --find-links https://wheel-index.linuxserver.io/alpine-3.24/ \
    mysqlclient && \
  printf "Helvio88/babybuddy version: ${VERSION}\nBuild-date: ${BUILD_DATE}" > /build_version && \
  echo "**** cleanup ****" && \
  apk del --purge \
    build-dependencies && \
  rm -rf \
    /tmp/* \
    $HOME/.cache \
    $HOME/.cargo \
    /app/www/public/.git \
    /app/www/public/node_modules \
    /app/www/public/docker

COPY docker/root/ /

EXPOSE 8000
VOLUME /config
