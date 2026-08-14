# Changelog

## Unreleased

### Changed

- In-app navigation now uses Hotwire Turbo Drive so clicking nav, cards, and
  links swaps the page without a full browser reload. Prefetch on hover/touch
  is enabled. Login, logout, file uploads, the API browser, and Django admin
  still do a full reload.

### Performance

- Load Plotly only on report pages, and only the current language locale instead
  of bundling every Plotly locale into `graph.js`.
- Defer vendor/app JavaScript so first paint is not blocked; load Masonry only
  on the child dashboard.
- Avoid N+1 child/tag queries on the timeline and stop loading full model rows
  for dashboard statistics.

### Docker

- Add a linuxserver/babybuddy-compatible `Dockerfile` that installs this
  repository (PUID/PGID/TZ/CSRF_TRUSTED_ORIGINS, `/config`, port 8000,
  default `admin`/`admin`). The image uses the same s6-overlay service
  wiring as `lscr.io/linuxserver/babybuddy` so gunicorn starts on boot.
