<!--
Copyright (c) 2026 8848 Digital LLP. All rights reserved.
Proprietary and confidential. Unauthorized copying, distribution, or use
of this file, via any medium, is strictly prohibited without prior
written permission from 8848 Digital LLP.
-->

# Keycloak Integration

## Purpose

Keycloak single sign-on, real-time user/role/session sync pushed by the
Keycloak listener (and again at each login), Role Profile ↔ Keycloak client
role sync, single logout, and bulk User Permissions.

## DocTypes

| DocType | Purpose |
| ------- | ------- |
| Erpnext Keycloak Role Profile Mapping | Role Profile ↔ Keycloak client role (id and name). |
| User Role Profiles | Role Profiles a user received from Keycloak (child: Role Profiles Table). |
| Permission Type | DocTypes that can be restricted together (child: Permission Type Doctype). |
| User and Permission Configuration | Creates User Permissions for a user (child: User Permission Doctype Value). |

## Customizations

| DocType | Owned by | What's customized |
| ------- | -------- | ------------------ |
| Role Profile | Frappe core | Creates/deletes the Keycloak client role; refreshes users' roles on change. |
| Social Login Key | Frappe core | Derives Base URL ↔ Root URL + Realm Name for the "keycloak" key; custom fields `enable_keycloak`, `root_url`, `realm_name`, `logout_url`. |
| User Permission | Frappe core | Blocks deleting records owned by a User and Permission Configuration. |

## Other code

- `api/v1/oauth.py` — overrides Frappe's `login_via_keycloak`: runs the standard flow, keeps the userinfo for role sync, remembers Keycloak's session.
- `api/v1/sdk.py` — endpoint for the listener's events (`keycloak_events`) and `access_token`.
- `sync/keycloak_events.py` — applies pushed events: upsert user (with roles), disable, logout.
- `patches/remove_unused_doctypes.py` — drops the DocTypes of the old push-sync design.
- `api/v1/user_and_permission_configuration.py` — DocType search query for the form.
- `sync/role_claims.py` — maps the token's client roles to Role Profiles.
- `login.py` / `sso_session.py` — `on_login` (role sync, User Permission rule) and `on_logout` hooks.
