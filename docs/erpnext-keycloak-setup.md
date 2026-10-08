<!--
Copyright (c) 2026 8848 Digital LLP. All rights reserved.
Proprietary and confidential. Unauthorized copying, distribution, or use
of this file, via any medium, is strictly prohibited without prior
written permission from 8848 Digital LLP.
-->

# Keycloak setup in ERPNext

This guide configures an ERPNext site for Keycloak single sign-on, real-time
user and role sync, and User Permission management. Set up Keycloak first:
see [keycloak-setup.md](./keycloak-setup.md).

The examples use the local test environment:

| Item | Example value |
| ---- | ------------- |
| ERPNext site | `http://127.0.0.1:8010` (`keycloak.localhost`) |
| Keycloak | `http://127.0.0.1:8080`, realm `erp` |
| Keycloak client of the site | `erpnext` |
| Keycloak site group | `site1` |
| Company | `8848 Digital LLP` |

## Contents

1. [Install the app](#1-install-the-app)
2. [Create the API user for the listener](#2-create-the-api-user-for-the-listener)
3. [Configure the Social Login Key](#3-configure-the-social-login-key)
4. [Create Role Profiles](#4-create-role-profiles)
5. [Give users access: User Permissions](#5-give-users-access-user-permissions)
6. [Log in and log out](#6-log-in-and-log-out)
7. [What syncs, and when](#7-what-syncs-and-when)
8. [Worked example](#8-worked-example)
9. [DocType reference](#9-doctype-reference)
10. [API reference](#10-api-reference)
11. [Troubleshooting](#11-troubleshooting)

## 1. Install the app

```shell
cd frappe-bench
bench get-app keycloak https://github.com/8848digital/keycloak-integration-python
bench --site keycloak.localhost install-app keycloak
bench --site keycloak.localhost set-config host_name "http://127.0.0.1:8010"
```

`host_name` must be the URL that browsers use for the site. It must equal
the Keycloak client's Root URL and the site group's `base_url`.

When you upgrade from 0.0.x, run `bench --site <site> migrate`. The patch
`remove_unused_doctypes` deletes Erpnext Keycloak User Mapping, Keycloak
Erpnext Group Mapping and Module Profile Name.

## 2. Create the API user for the listener

The Keycloak event listener calls ERPNext as this user. The user must have
the **System Manager** role.

1. **User → Add User.** Email `keycloak-sync@example.com`, first name
   `Keycloak Sync`. Add the role **System Manager**. Save.
2. **Settings** tab → **API Access** → **Generate Keys**. Copy the API
   secret now; ERPNext shows it only once. The API key stays on the form.
3. In Keycloak, put the key and the secret on the site group
   (`client_id`, `client_secret`). See
   [keycloak-setup.md §7.6](./keycloak-setup.md#76-create-the-site-group).

## 3. Configure the Social Login Key

**Social Login Key → Add Social Login Key**, then select Social Login
Provider **Keycloak**. ERPNext fills in the standard URLs. Complete the form:

| Field | Example | Notes |
| ----- | ------- | ----- |
| Social Login Provider | `Keycloak` | Built-in provider. You cannot change it after save. |
| Provider Name | `Keycloak` | Gives the record name `keycloak`, which the app uses. |
| Enable Social Login | ✔ | Shows **Login with Keycloak** on `/login`. |
| Client ID | `erpnext` | The Keycloak client. |
| Client Secret | (from Keycloak → Clients → erpnext → Credentials) | |
| Custom Base URL | ✔ | |
| Base URL | `http://127.0.0.1:8080/realms/erp` | The URL browsers use for Keycloak. |
| Authorize URL | `/protocol/openid-connect/auth` | Preset. |
| Access Token URL | `/protocol/openid-connect/token` | Preset. |
| Redirect URL | `/api/method/frappe.integrations.oauth2_logins.login_via_keycloak` | Preset. |
| API Endpoint | `/protocol/openid-connect/userinfo` | Preset. |
| User ID Property | `sub` | Links ERPNext users to the Keycloak user id. |
| Sign ups | `Allow` | First-time users are created at login. |
| Enable Keycloak | ✔ | App field. Turns on the Admin API calls (roles, logout). |
| Root URL / Realm Name | `http://127.0.0.1:8080/` / `erp` | App fields. Filled in from Base URL on save. |

Save. Open `/login` in a private window: the **Login with Keycloak** button
is there.

## 4. Create Role Profiles

A Role Profile is a named set of roles. Each Role Profile is a client role of
the site's Keycloak client, with the same name.

1. **Role Profile → Add Role Profile.** Name `Demo Sales Head`, roles
   `Sales User`, `Sales Manager`. Save.
2. ERPNext creates the client role `Demo Sales Head` on the client `erpnext`
   and stores the link in **Erpnext Keycloak Role Profile Mapping**.
3. In Keycloak, grant the role to users or groups (see
   [keycloak-setup.md §8](./keycloak-setup.md#8-manage-users-and-access)).

| You do in ERPNext | Result |
| ----------------- | ------ |
| Create a Role Profile | Client role created in Keycloak. If Keycloak refuses, the Role Profile is not saved. |
| Change the roles of a Role Profile | Every user with that Role Profile gets the new roles (background job, seconds). |
| Delete a Role Profile | Client role deleted in Keycloak. |

A user with several Role Profiles gets all of their roles. ERPNext replaces
the roles of a Keycloak-managed user with the roles of their Role Profiles;
do not add roles to those users by hand. Users that never got a Role Profile
from Keycloak (for example local admins) keep their manual roles.

## 5. Give users access: User Permissions

The app lets a user log in only when the user has at least one **User
Permission** (Administrator is exempt). Use Permission Types to give the same
kind of access to many users.

### 5.1 Permission Type

A Permission Type lists the DocTypes that you restrict together.

**Permission Type → Add.** Example `PT Company and Warehouse`:

| Allow DocType | Apply To All Doctypes | Applicable For | Hide Descendants | Is Default |
| ------------- | --------------------- | -------------- | ---------------- | ---------- |
| Company | ✔ | | | |
| Warehouse | ✔ | | ✔ | |

Rules:

- Each DocType once per Permission Type.
- **Applicable For** needs **Apply To All Doctypes** off.
- **Hide Descendants** only for tree DocTypes (Warehouse, Territory, Cost Center, …).
- You cannot change or remove a row that a configuration uses. Remove the
  configuration rows first.

### 5.2 User and Permission Configuration

**User and Permission Configuration → Add.** Example:

| Field | Value |
| ----- | ----- |
| User | `jane@example.com` |
| Permission Type | `PT Company and Warehouse` |
| Rows | `Company` → `8848 Digital LLP`; `Warehouse` → `Stores - 8DLD` |

On save, ERPNext creates one **User Permission** per row (the name is shown
in the row). Removing a row deletes its User Permission; deleting the
configuration deletes all of them. You cannot delete these User Permissions
directly, only through the configuration.

## 6. Log in and log out

### First login of a new person

1. The admin creates the person in Keycloak, adds them to the site group or
   grants a client role. ERPNext creates the user at once (real time).
2. The admin adds a User and Permission Configuration for the user.
3. The person opens ERPNext → **Login with Keycloak** → signs in → lands on the desk.

If step 2 is missing, the person sees **"Access not set up"** (HTTP 403). The
user and their roles stay in ERPNext, so the admin can add the access; the
Keycloak session is ended. After step 2, the person signs in again.

### Logout

| Action | Result |
| ------ | ------ |
| Logout in ERPNext | ERPNext session ends, and the Keycloak session ends ("Logged out successfully from Keycloak"). |
| Logout in Keycloak, or admin **Sign out** in Keycloak | All ERPNext sessions of the user end at once. |
| User disabled in Keycloak | User disabled in ERPNext; sessions end. |

## 7. What syncs, and when

| Change | Direction | When |
| ------ | --------- | ---- |
| User created / added to site group / name changed | Keycloak → ERPNext | Real time (listener) |
| Client role granted or removed (user or group, incl. group membership) | Keycloak → ERPNext | Real time (listener), and again at each login |
| User disabled / deleted | Keycloak → ERPNext | Real time: disabled, sessions ended |
| Logout in Keycloak / admin Sign out | Keycloak → ERPNext | Real time: sessions ended |
| Role Profile created / deleted | ERPNext → Keycloak | Immediately (client role) |
| Role Profile roles changed | ERPNext users | Seconds (background job) |
| Logout in ERPNext | ERPNext → Keycloak | Immediately |

If ERPNext is down when the listener sends a change, the change is logged in
Keycloak and applied at the user's next login.

## 8. Worked example

The local test environment has this demo data. You can create the same with
the steps below.

**Role Profiles (each one is a client role of `erpnext`):**

| Role Profile | Roles |
| ------------ | ----- |
| Demo Sales Executive | Sales User |
| Demo Sales Head | Sales User, Sales Manager |
| Demo Purchase Executive | Purchase User |
| Demo Purchase Head | Purchase User, Purchase Manager |
| Demo Store Keeper | Stock User |
| Demo Stock Head | Stock User, Stock Manager, Item Manager |
| Demo Accountant | Accounts User |
| Demo Finance Head | Accounts User, Accounts Manager, Auditor |
| Demo HR Executive | HR User |
| Demo HR Head | HR User, HR Manager |
| Demo Project Lead | Projects User, Projects Manager |
| Demo Support Analyst | Support Team, Report Manager, Analytics |

**Keycloak teams (groups that grant client roles):**

| Group | Client roles | Members |
| ----- | ------------ | ------- |
| Sales Team | Demo Sales Executive | team.sales1, team.sales2, team.sales3 |
| Stores Team | Demo Store Keeper | team.store1, team.store2 |
| Finance Team | Demo Accountant | team.fin1, team.fin2 |
| Managers | Demo Sales Head, Demo Finance Head | team.manager1 |

**Access (User and Permission Configuration):** every team user has
`PT Company` → `8848 Digital LLP`.

Steps for one person, Jane in the Sales Team:

1. Keycloak: **Users → Add user** `jane`, e-mail `jane@example.com`,
   **Join groups** → `site1` and `Sales Team`. Set a password.
2. ERPNext shows user `jane@example.com` with role **Sales User** (from
   Demo Sales Executive), linked to Keycloak.
3. ERPNext: **User and Permission Configuration** → User `jane@example.com`,
   Permission Type `PT Company`, row `Company` = `8848 Digital LLP`. Save.
4. Jane signs in with **Login with Keycloak** and lands on the desk.
5. Keycloak: move Jane to `Managers`. ERPNext at once gives her Sales
   Manager, Accounts Manager and Auditor.

`docs/scripts/create-demo-data.py` creates this data through the real flows.

## 9. DocType reference

| DocType | Purpose | Written by |
| ------- | ------- | ---------- |
| Erpnext Keycloak Role Profile Mapping | Role Profile ↔ Keycloak client role (name and id). | Role Profile create |
| User Role Profiles (+ Role Profiles Table) | The Role Profiles a user has from Keycloak. | Listener push and login |
| Permission Type (+ Permission Type Doctype) | DocTypes restricted together. | Admin |
| User and Permission Configuration (+ User Permission Doctype Value) | A user's User Permissions for one Permission Type. | Admin |

Standard DocTypes used: **Social Login Key**, **User** (table **User Social
Login** links the user to the Keycloak id), **Role Profile**, **User Permission**.

## 10. API reference

All calls go to `POST /api/method/keycloak.sdk.api` (alias of
`keycloak.keycloak_integration.api.v1.sdk.api`).

Every response uses the standard 8848 envelope `{status, status_code,
message, data, errors}` (the app's `after_request` hook); the result is under
`data`. Errors keep their HTTP status (403 not permitted, 417 validation).

**Keycloak events** (System Manager only; sent by the listener):

```shell
curl -X POST http://127.0.0.1:8010/api/method/keycloak.sdk.api \
  -H "Authorization: token <api_key>:<api_secret>" -H "Content-Type: application/json" \
  -d '{"version":"v1","entity":"keycloak_events","method":"handle_event",
       "operation":"upsert_user",
       "user":{"id":"8c1f…","username":"jane","email":"jane@example.com","firstName":"Jane","enabled":true},
       "roles":["Demo Sales Executive"]}'
# {"status":true,"status_code":200,"message":"Request processed successfully",
#  "data":{"user":"jane@example.com","operation":"upsert_user","exec_time":"0.08 seconds"},"errors":null}
```

**Access token** (Guest; rate-limited to 10 calls per 10 minutes per IP):

```shell
curl -X POST http://127.0.0.1:8010/api/method/keycloak.sdk.api \
  -H "Content-Type: application/json" \
  -d '{"version":"v1","entity":"access_token","method":"get_access_token","usr":"jane@example.com","pwd":"..."}'
# {"status":true,"status_code":200,"message":"Request processed successfully",
#  "data":{"msg":"success","data":{"access_token":"token <key>:<secret>"}, ...},"errors":null}
```

It returns the user's existing API key and secret. Users created through
Keycloak have a random ERPNext password, so this call is for local accounts.

## 11. Troubleshooting

| Problem | Cause and fix |
| ------- | ------------- |
| No **Login with Keycloak** button | Enable Social Login is off, or the Social Login Key is not named `keycloak`. |
| "Access not set up" | The user has no User Permission. Add a User and Permission Configuration. |
| "Signup is Disabled" | Set **Sign ups** to `Allow` on the Social Login Key. |
| Role Profile save fails with "Keycloak rejected the role" | The client's service account needs `manage-clients` and `view-clients`. |
| "Keycloak client erpnext not found" | Client ID on the Social Login Key does not exist in the realm. |
| Logout message "Logout from Keycloak failed" | The service account needs `manage-users`. See **Error Log** → "SSO Logout Error". |
| Roles not applied at login | Error Log "Keycloak role sync skipped": add the client-roles mapper with **Add to userinfo** on. |
| Push from Keycloak does nothing | Check the Keycloak log. 403 = API user is not System Manager; connection refused = `base_url` not reachable from Keycloak. |
| User Permission cannot be deleted | It belongs to a User and Permission Configuration; edit that instead. |
