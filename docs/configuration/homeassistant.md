# Home Assistant

## `HOME_ASSISTANT_USE_X_INGRESS_PATH`

*Default:* `False`

This setting should be set to `True` if babybuddy is hosted through the [ingress
service of home assistant](https://developers.home-assistant.io/docs/add-ons/presentation/#ingress).

This setting is necessary so that babybuddy can build correct absolute paths to
itself when run in home assistant. The ingress routing of home assistant
otherwise will obfuscate the true host-url and some functions, like the QR-code
generator for coupling devices might not work correctly.

**Do not enable this feature on other setups.** Attackers might be able to
use this feature to redirect traffic in unexpected ways by manually adding
`X-Ingress-Path` to the request URL.
