<!--
Copyright (c) 2026 8848 Digital LLP. All rights reserved.
Proprietary and confidential. Unauthorized copying, distribution, or use
of this file, via any medium, is strictly prohibited without prior
written permission from 8848 Digital LLP.
-->

# Keycloak Integration

## Overview

Connects ERPNext to Keycloak. Users sign in with Keycloak single sign-on
(Frappe's built-in Keycloak provider). Keycloak decides who can use the site
and with which Role Profiles: a Keycloak event listener pushes every user,
group, role and logout change to ERPNext in real time, and each login applies
the roles from the login token again. Signing out of either system signs the
user out of both.

The Keycloak side is the event listener in
[keycloak-integration-java](https://github.com/8848digital/keycloak-integration-java).
Full guides: [docs/](./docs/README.md).

## Key DocTypes

| DocType | Owned by this app? | Purpose |
| ------- | ------------------ | ------- |
| Erpnext Keycloak Role Profile Mapping | Yes | Links a Role Profile to its Keycloak client role. |
| User Role Profiles | Yes | The Role Profiles a user has from Keycloak. |
| Permission Type | Yes | A named set of DocTypes that can be restricted for a user. |
| User and Permission Configuration | Yes | Gives a user the User Permissions of a Permission Type. |
| Role Profile | No (Frappe, customized) | Creating or deleting one creates or deletes the Keycloak client role. |
| Social Login Key | No (Frappe, customized) | The "keycloak" key (built-in Keycloak provider) holds the Keycloak address and client. |
| User | No (Frappe) | Standard "User Social Login" table links the user to the Keycloak id. |
| User Permission | No (Frappe, customized) | Records owned by a configuration cannot be deleted directly. |

## Features

- Sign in to ERPNext with Keycloak; first-time users are created automatically.
- Real time from Keycloak: new users, group membership, client role grants
  (on users or groups), name changes, disable and delete reach ERPNext at once.
- Each ERPNext Role Profile is a client role of the site's Keycloak client.
  Several Role Profiles give the combined roles.
- Creating or deleting a Role Profile creates or deletes the Keycloak client role.
- Single logout in both directions: ERPNext logout ends the Keycloak session;
  Keycloak logout, admin sign-out or disable ends the ERPNext sessions.
- Allow sign-in only to users who have at least one User Permission
  (Administrator excepted).
- Manage User Permissions in bulk with Permission Types and User and
  Permission Configurations.

## Integrations

- **Keycloak (identity provider, Admin API, event listener)** — see [SETUP.md](./SETUP.md#keycloak)

## Installation

    bench get-app keycloak https://github.com/8848digital/keycloak-integration-python
    bench --site <site_name> install-app keycloak

## App Structure

See [CLAUDE.md](./CLAUDE.md) for internal module/folder layout and coding conventions.

## Maintainers

8848 Digital LLP — Satyabrata Panda (satya@8848digital.com)

## License

Proprietary — Copyright (c) 2026 8848 Digital LLP. All rights reserved.
See [license.txt](license.txt) for details.
