<!--
Copyright (c) 2026 8848 Digital LLP. All rights reserved.
Proprietary and confidential. Unauthorized copying, distribution, or use
of this file, via any medium, is strictly prohibited without prior
written permission from 8848 Digital LLP.
-->

# SETUP.md

## Keycloak

### Overview

ERPNext uses Frappe's built-in Keycloak login provider, reads the user's
client roles from the login token, and calls the Keycloak Admin REST API to
manage client roles and end sessions. The Keycloak event listener pushes
changes to ERPNext in real time. Step-by-step guides with examples:
[docs/keycloak-setup.md](./docs/keycloak-setup.md) and
[docs/erpnext-keycloak-setup.md](./docs/erpnext-keycloak-setup.md).

### Required Credentials

| Credential | Where it's stored | Required? |
| ---------- | ------------------ | --------- |
| Keycloak client ID / secret | Social Login Key "keycloak" → Client ID / Client Secret | Yes |
| ERPNext API key / secret of a **System Manager** (listener's API user) | Keycloak site group attributes `client_id` / `client_secret` | Yes |
| Listener encryption key | Keycloak env `KC_SPI_EVENTS_LISTENER_CUSTOM_EVENT_LISTENER_ENCRYPTION_KEY` | Yes |

### Settings DocType Fields

Social Login Key with Social Login Provider **Keycloak** (name "keycloak"):

| Field | Type | Mandatory | Notes |
| ----- | ---- | --------- | ----- |
| Enable Social Login | Check | Yes | Shows "Login with Keycloak". |
| Enable Keycloak (`enable_keycloak`) | Check | Yes | Turns the Admin API calls on (roles, logout). |
| Base URL | Data | Yes | `<keycloak>/realms/<realm>`. Root URL and Realm Name are filled in from it. |
| Client ID / Client Secret | Data / Password | Yes | The site's confidential client. |
| User ID Property | Data | Yes | `sub` (Keycloak user id). |
| Sign ups | Select | Yes | `Allow`. |

### Keycloak realm requirements

| Item | Value |
| ---- | ----- |
| Site client | Confidential, standard flow, service account; **Root URL = site URL**. |
| Service-account roles (realm-management) | `manage-clients`, `view-clients`, `manage-users`. |
| Client-roles mapper | User Client Role, claim `resource_access.${client_id}.roles`, **Add to userinfo** on. |
| Events | Listener `custom-event-listener`; admin events on, with representation. |
| Site group | Top-level group, attributes `base_url` (= site URL), `client_id`, `client_secret`. |

`docs/scripts/setup-keycloak-realm.sh` sets all of this up.

### Site Config / Environment Variables

| Key | Scope | Notes |
| --- | ----- | ----- |
| `host_name` | Per site | Must equal the client's Root URL and the group's `base_url`. |

### Webhooks (if applicable)

The Keycloak listener POSTs to `/api/method/keycloak.sdk.api`
(`entity=keycloak_events`), authenticated with the site group's API key and
secret. See [docs/erpnext-keycloak-setup.md §10](./docs/erpnext-keycloak-setup.md#10-api-reference).

### How to Test

1. Create a Role Profile; a client role with the same name appears in Keycloak.
2. In Keycloak, add a user to the site group and grant the role; the user
   appears in ERPNext with the roles at once.
3. Add a User and Permission Configuration, then sign in with "Login with Keycloak".
