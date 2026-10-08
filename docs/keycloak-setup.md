<!--
Copyright (c) 2026 8848 Digital LLP. All rights reserved.
Proprietary and confidential. Unauthorized copying, distribution, or use
of this file, via any medium, is strictly prohibited without prior
written permission from 8848 Digital LLP.
-->

# Keycloak setup and run

This guide sets up Keycloak for the Keycloak Integration app: it runs
Keycloak, installs the event listener, and configures a realm for one or more
ERPNext sites. For the ERPNext side, see
[erpnext-keycloak-setup.md](./erpnext-keycloak-setup.md).

## Contents

1. [How it works](#1-how-it-works)
2. [Requirements](#2-requirements)
3. [Build the event listener](#3-build-the-event-listener)
4. [Run Keycloak locally (Docker)](#4-run-keycloak-locally-docker)
5. [Run Keycloak in production](#5-run-keycloak-in-production)
6. [Configure the realm (script)](#6-configure-the-realm-script)
7. [Configure the realm (admin console)](#7-configure-the-realm-admin-console)
8. [Manage users and access](#8-manage-users-and-access)
9. [Configuration reference](#9-configuration-reference)
10. [Check the setup](#10-check-the-setup)
11. [Troubleshooting](#11-troubleshooting)

## 1. How it works

```
             browser SSO (OpenID Connect, standard)
  ┌────────┐ ───────────────────────────────────────► ┌──────────────┐
  │ERPNext │ ◄─────────────────────────────────────── │   Keycloak   │
  │  site  │   login token: client roles of the site   │  realm "erp" │
  │        │                                            │              │
  │        │ ── Admin REST API: create/delete client ─► │              │
  │        │    roles, end session on logout            │              │
  │        │                                            │  event       │
  │        │ ◄─ real-time push (after commit) ───────── │  listener    │
  └────────┘    users, roles, disable, logout           └──────────────┘
```

| Keycloak object | Means in ERPNext |
| --------------- | ---------------- |
| Client (one per ERPNext site, Root URL = site URL) | The site. Its OIDC client for SSO. |
| Client role of that client | One ERPNext **Role Profile** with the same name. |
| Top-level group with attribute `base_url` | The site, for the event listener. Holds the site's API credentials. |
| Group membership / client role grant | Access to the site, and the user's Role Profiles. |

- **Login (standard):** ERPNext uses Frappe's built-in Keycloak provider.
  The user's client roles come in the claim `resource_access.<client>.roles`.
  ERPNext creates a first-time user and sets their Role Profiles at each login.
- **Real time (event listener):** when an admin changes a user, a group
  membership or a client role grant, or a user logs out, the listener sends
  the change to ERPNext at once. ERPNext updates the user, their roles, and
  ends their sessions when they are disabled or logged out.
- **Logout:** logging out of ERPNext ends the Keycloak session, and logging
  out of Keycloak ends the ERPNext sessions.

## 2. Requirements

| Item | Version |
| ---- | ------- |
| Keycloak | 24.0.4 (the listener is built against this version) |
| Java / Maven | JDK 17 and Maven 3.9, or Docker |
| Database | PostgreSQL 14+ (the Docker setup uses PostgreSQL 16) |
| Event listener | `custom-event-listener.jar` from [keycloak-integration-java](https://github.com/8848digital/keycloak-integration-java) |

## 3. Build the event listener

```shell
git clone https://github.com/8848digital/keycloak-integration-java
cd keycloak-integration-java
mvn clean package
# or, without Maven:
docker run --rm -v "$PWD":/src -w /src maven:3.9-eclipse-temurin-17 mvn -B clean package
```

The result is `target/custom-event-listener.jar`.

## 4. Run Keycloak locally (Docker)

The repo contains a development stack (Keycloak 24.0.4 + PostgreSQL) with the
jar mounted from `target/`.

1. Create the settings file and change every value:

   ```shell
   cp src/main/docker/.env.example src/main/docker/.env
   ```

   ```ini
   KEYCLOAK_ADMIN=admin
   KEYCLOAK_ADMIN_PASSWORD=<strong password>
   KC_DB_PASSWORD=<strong password>
   KC_DB_PORT=5433
   KC_HTTP_PORT=8080
   KC_LISTENER_ENCRYPTION_KEY=<long random string, keep it>
   KC_LISTENER_ADMIN_CLIENT_ID=keycloak_client
   # Windows + WSL2 only, so the Windows browser can reach Keycloak:
   KC_HTTP_HOST=0.0.0.0
   KC_JAVA_OPTS_APPEND=-Djava.net.preferIPv4Stack=true
   ```

   Make a random value with `openssl rand -hex 32`.

2. Start the stack:

   ```shell
   docker compose --env-file src/main/docker/.env -f src/main/docker/docker-compose.yml up -d
   ```

3. Open `http://127.0.0.1:8080/admin/` and log in with `KEYCLOAK_ADMIN` /
   `KEYCLOAK_ADMIN_PASSWORD`.

| Command | Purpose |
| ------- | ------- |
| `docker compose ... logs -f keycloak` | Follow the Keycloak log. |
| `docker compose ... restart keycloak` | Reload after you rebuild the jar. |
| `docker compose ... down` | Stop (data stays in the `keycloak-db` volume). |

The stack uses host networking. Keycloak can then call an ERPNext bench on
`localhost`, and ERPNext can call Keycloak on `localhost:8080`.

## 5. Run Keycloak in production

1. Copy `custom-event-listener.jar` to Keycloak's `providers/` folder.
2. Set the listener settings as environment variables (see
   [Configuration reference](#9-configuration-reference)).
3. Build and start in production mode, behind HTTPS:

   ```shell
   bin/kc.sh build --db=postgres
   bin/kc.sh start --hostname=sso.example.com \
       --db-url=jdbc:postgresql://db/keycloak --db-username=keycloak --db-password=...
   ```

- Do not use `start-dev` in production.
- Use the same `KC_SPI_EVENTS_LISTENER_CUSTOM_EVENT_LISTENER_ENCRYPTION_KEY`
  on every Keycloak node. If you change it, enter the ERPNext API secrets on
  the site groups again.
- ERPNext sites must be reachable from Keycloak (the listener calls them), and
  Keycloak must be reachable from ERPNext and from the browsers.

## 6. Configure the realm (script)

`docs/scripts/setup-keycloak-realm.sh` (in the keycloak-integration-python
repo) does all of [section 7](#7-configure-the-realm-admin-console) with
Keycloak's admin CLI. You can run it more than once.

Before you run it, create the listener's API user in ERPNext and get its API
key and secret (see
[erpnext-keycloak-setup.md, step 2](./erpnext-keycloak-setup.md#2-create-the-api-user-for-the-listener)).

```shell
KC_CONTAINER=keycloak-erpnext-keycloak-1 \
KEYCLOAK_ADMIN_PASSWORD='<admin password>' \
REALM=erp \
SITE_URL=http://127.0.0.1:8010 \
CLIENT_ID=erpnext \
SITE_GROUP=site1 \
ERPNEXT_API_KEY='<api key>' \
ERPNEXT_API_SECRET='<api secret>' \
docs/scripts/setup-keycloak-realm.sh
```

The script prints the client secret. Enter it in ERPNext. For a second site,
run the script again with that site's `SITE_URL`, `CLIENT_ID`, `SITE_GROUP`
and API credentials.

## 7. Configure the realm (admin console)

Do these steps once per realm (7.1, 7.5) and once per ERPNext site (7.2–7.4).

### 7.1 Create the realm

1. In the realm list (top left), click **Create realm**.
2. **Realm name:** `erp`. Click **Create**.

### 7.2 Create the site's client

1. **Clients → Create client.**
2. **General settings:** Client type `OpenID Connect`, Client ID `erpnext`. **Next.**
3. **Capability config:** Client authentication **On**, Standard flow **On**,
   Direct access grants **Off**, Service accounts roles **On**. **Next.**
4. **Login settings:**

   | Field | Example |
   | ----- | ------- |
   | Root URL | `http://127.0.0.1:8010` (exactly the site's `host_name`) |
   | Valid redirect URIs | `http://127.0.0.1:8010/*` |
   | Valid post logout redirect URIs | `+` |
   | Web origins | `http://127.0.0.1:8010` |

5. **Save.** Open the **Credentials** tab and copy the **Client secret**.

### 7.3 Give the client's service account its roles

ERPNext uses this account to create and delete client roles, and to end
sessions on logout.

1. **Clients → erpnext → Service accounts roles → Assign role.**
2. **Filter by clients**, search `realm-management`, select
   `manage-clients`, `view-clients`, `manage-users`. **Assign.**

### 7.4 Put the client roles in the token

1. **Clients → erpnext → Client scopes → erpnext-dedicated → Add mapper → By configuration → User Client Role.**
2. Fill in:

   | Field | Value |
   | ----- | ----- |
   | Name | `erpnext client roles` |
   | Client ID | `erpnext` |
   | Token Claim Name | `resource_access.${client_id}.roles` |
   | Claim JSON Type | `String` |
   | Multivalued | On |
   | Add to ID token / access token / userinfo | On / On / **On** |

3. **Save.** ERPNext reads the claim from **userinfo**, so that switch is required.

### 7.5 Turn on the event listener

1. **Realm settings → Events → Event listeners:** add `custom-event-listener`. **Save.**
2. **Admin events settings** tab: **Save events** On, **Include representation** On. **Save.**

### 7.6 Create the site group

1. **Groups → Create group**, name `site1`. The listener adds three
   placeholder attributes.
2. Open the group → **Attributes**, and set:

   | Key | Value |
   | --- | ----- |
   | `base_url` | `http://127.0.0.1:8010` (same as the client's Root URL) |
   | `client_id` | ERPNext API key of the listener's API user |
   | `client_secret` | ERPNext API secret of that user |

3. **Save.** The listener replaces `client_secret` with an encrypted value
   that starts with `v2:`.

## 8. Manage users and access

| You do in Keycloak | ERPNext result (in real time) |
| ------------------ | ----------------------------- |
| Create a user and add them to `site1` | User created, linked to the Keycloak id. |
| **Users → user → Role mapping → Assign role → Filter by clients → `erpnext`**, pick a role | The Role Profile with that name is given; the user's roles are rebuilt. |
| Grant a client role to a group (**Groups → group → Role mapping**) | Every member gets the Role Profile. Add or remove members to change access. |
| Remove a role or a group membership | The Role Profile is taken away. A user with no site group and no roles is disabled. |
| Edit first or last name | Updated. |
| Turn **Enabled** off | User disabled; open ERPNext sessions end. |
| **Users → user → Sessions → Sign out**, or the user logs out of Keycloak | Open ERPNext sessions end. |
| Delete the user | User disabled in ERPNext (history is kept). |

You create the client roles from ERPNext: every new Role Profile creates a
client role with the same name. You can also create a client role by hand
with the exact name of an existing Role Profile.

Example of a team set-up:

| Keycloak group | Client roles of `erpnext` granted to the group |
| -------------- | ---------------------------------------------- |
| `Sales Team` | `Demo Sales Executive` |
| `Sales Managers` | `Demo Sales Head` |
| `Stores Team` | `Demo Store Keeper` |
| `Finance Team` | `Demo Accountant`, `Demo Finance Head` |

Add a person to `Sales Team` and they can use ERPNext as a Sales User at once.

## 9. Configuration reference

Event listener settings (environment variables of the Keycloak server):

| Variable | Default | Purpose |
| -------- | ------- | ------- |
| `KC_SPI_EVENTS_LISTENER_CUSTOM_EVENT_LISTENER_ENCRYPTION_KEY` | none (required) | Encrypts the ERPNext API secrets on site groups. Any long random string. |
| `KC_SPI_EVENTS_LISTENER_CUSTOM_EVENT_LISTENER_ERPNEXT_API_PATH` | `/api/method/keycloak.sdk.api` | ERPNext endpoint the listener calls. |
| `KC_SPI_EVENTS_LISTENER_CUSTOM_EVENT_LISTENER_TIMEOUT_MS` | `10000` | Connect and read timeout for calls to ERPNext. |
| `KC_SPI_EVENTS_LISTENER_CUSTOM_EVENT_LISTENER_ADMIN_CLIENT_ID` | `keycloak_client` | Not used by the current listener; kept for compatibility. |

Docker stack settings (`src/main/docker/.env`):

| Key | Purpose |
| --- | ------- |
| `KEYCLOAK_ADMIN`, `KEYCLOAK_ADMIN_PASSWORD` | First admin of the master realm. |
| `KC_DB_PASSWORD`, `KC_DB_PORT` | PostgreSQL password and host port (default 5433). |
| `KC_HTTP_PORT`, `KC_HTTP_HOST` | Keycloak port (8080) and bind address (127.0.0.1; 0.0.0.0 for WSL2). |
| `KC_LISTENER_ENCRYPTION_KEY` | Passed to the listener's encryption key. |
| `KC_JAVA_OPTS_APPEND` | Extra JVM flags (`-Djava.net.preferIPv4Stack=true` for WSL2). |

What the listener sends to ERPNext (`POST <base_url>/api/method/keycloak.sdk.api`,
header `Authorization: token <client_id>:<client_secret>`):

```json
{
  "version": "v1",
  "entity": "keycloak_events",
  "method": "handle_event",
  "operation": "upsert_user",
  "user": {"id": "8c1f…", "username": "jane", "email": "jane@example.com",
           "firstName": "Jane", "lastName": "Doe", "enabled": true},
  "roles": ["Demo Sales Head"]
}
```

`operation` is `upsert_user`, `disable_user` or `logout_user`. When `roles` is
missing, ERPNext keeps the user's roles. The listener sends after Keycloak
commits; a failed call is logged in the Keycloak log, and the next login
corrects the user.

## 10. Check the setup

1. `docker compose ... logs keycloak | grep custom-event-listener` shows the
   provider (the warning about an internal SPI is normal).
2. The site group's `client_secret` starts with `v2:`.
3. Create a test user, add them to the site group: the user appears in
   ERPNext **User** within a second.
4. Log in to ERPNext with **Login with Keycloak**.

## 11. Troubleshooting

| Problem | Cause and fix |
| ------- | ------------- |
| User does not appear in ERPNext | `base_url` of the site group must equal the client's Root URL and be reachable from Keycloak. Look for `ERPNext call … failed` or `answered HTTP 403` in the Keycloak log (403: the API user is not a System Manager). |
| `ERPNext site is not configured` in the log | The site group still has a placeholder value. |
| `Cannot encrypt the client secret` | `…_ENCRYPTION_KEY` is not set. |
| Roles do not change | The client role name must equal the Role Profile name, and the role must belong to the site's client. |
| Roles are set at push but not at login | The mapper is missing or **Add to userinfo** is off (ERPNext logs "Keycloak role sync skipped"). |
| "Invalid parameter: redirect_uri" | The client's Valid redirect URIs must cover the site URL. |
| Windows browser cannot open Keycloak (WSL2) | Set `KC_HTTP_HOST=0.0.0.0` and `KC_JAVA_OPTS_APPEND=-Djava.net.preferIPv4Stack=true`. |
