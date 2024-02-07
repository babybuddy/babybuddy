# Home Assistant

## `ENABLE_HOME_ASSISTANT_SUPPORT`

_Default:_ `False`

This setting should be set to `True` if babybuddy is hosted through the [ingress
service of home assistant](https://developers.home-assistant.io/docs/add-ons/presentation/#ingress).

This setting is necessary so that babybuddy can build correct absolute paths to
itself when run in home assistant. The ingress routing of home assistant
otherwise will obfuscate the true host-url and some functions, like the QR-code
generator for coupling devices might not work correctly.

In addition, the QR-Code that allows connecting external applications
to baby buddy will expose home assistant's ingress-service cookie
`ingress_session`. This cookie is created for a user visiting baby buddy through
home assistant. It allows a connecting application to authenticate with
home assistant's ingress service, which is a required extra step in
for this setup.

**Do not enable this feature on other setups.** Attackers might be able to
use this feature to redirect traffic in unexpected ways by manually adding
`X-Ingress-Path` to the request headers.
