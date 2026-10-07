# Login QR code

Baby Buddy can hand a device everything it needs to talk to your instance in a
single QR code, so a companion app can be paired by scanning instead of by
copying an API key around by hand. The code authenticates as one user, so what it
carries is that user's [API token](api.md#authentication).

## Where to find it

Sign in and open **User → Add a device** (`/user/add-device/`). The page shows two
things for the logged in user:

- **Key** — the user's API token. **Regenerate** replaces it.
- **Login QR code** — the code described on this page.

## What the code contains

The QR code holds a single line of text: the literal prefix `BABYBUDDY-LOGIN:`
followed by a JSON object.

```text
BABYBUDDY-LOGIN:{"url": "https://baby.example.com/", "api_key": "2h23807gd72h7hop382p98hd823dw3g665g56", "session_cookies": {}}
```

| Field | Type | Description |
| --- | --- | --- |
| `url` | string | Absolute base URL of the instance, with a trailing slash. |
| `api_key` | string | The user's API token — the same value shown as **Key**. |
| `session_cookies` | object | Cookies the app has to send back. Empty unless Home Assistant support is enabled, see [Home Assistant](configuration/homeassistant.md). |

## Reading it

Split the prefix off, parse the remainder as JSON, then use `api_key` exactly like
a token copied by hand.

```python
import json
import urllib.request
from urllib.parse import urljoin

raw = "BABYBUDDY-LOGIN:{...}"
prefix, _, payload = raw.partition(":")
assert prefix == "BABYBUDDY-LOGIN", "not a Baby Buddy login code"
config = json.loads(payload)

request = urllib.request.Request(
    urljoin(config["url"], "api/children/"),
    headers={"Authorization": "Token " + config["api_key"]},
)
print(urllib.request.urlopen(request).read().decode())
```

From there every endpoint listed in the [API documentation](api.md) is reachable,
with the same access as the user the token belongs to.

`session_cookies` is only populated for the Home Assistant ingress setup, where
the ingress service is what terminates the connection to Baby Buddy. An app handed
those cookies has to replay them on every request:

```python
if config["session_cookies"]:
    request.add_header(
        "Cookie",
        "; ".join("%s=%s" % item for item in config["session_cookies"].items()),
    )
```

## Where `url` comes from

`url` is assembled from the request that rendered the page rather than from a
setting of its own, so it is the host the user is browsing through. That is
usually what a device on the same network needs, but it does mean the request has
to arrive with the right details when Baby Buddy sits behind something else:

- [Proxy configuration](setup/proxy.md) — including
  `SECURE_PROXY_SSL_HEADER`, which decides whether the code says `https`.
- [Subdirectory configuration](setup/subdirectory.md) — the code then points at
  the subdirectory root.
- [Home Assistant](configuration/homeassistant.md) — required for ingress, where
  the real host URL is otherwise hidden.

## Keep it secret

The code is a credential, so treat it like the token inside it.

- Anyone who can photograph the screen can read the key out of the code, so pair
  devices over a channel you trust.
- **Regenerate** on the same page deletes the token and issues a new one. Every
  code generated before that stops working, and so does anything else using the
  old token.
- `api_key` is sent in a header, so serve Baby Buddy over `https` before pairing
  anything that is not on the same machine.
