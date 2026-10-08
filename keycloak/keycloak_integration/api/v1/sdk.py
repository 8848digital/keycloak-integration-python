# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.

"""Versioned entry point of the app's API (kept for existing clients)."""

import time

import frappe
from frappe import _

from keycloak.keycloak_integration.sync.access_token import get_access_token
from keycloak.keycloak_integration.sync.keycloak_events import handle_event
from keycloak.keycloak_integration.sync.responses import error_response

# (version, entity, method) -> handler. An explicit allow-list: the request
# can only reach these functions.
HANDLERS = {
	("v1", "access_token", "get_access_token"): get_access_token,
	("v1", "keycloak_events", "handle_event"): handle_event,
}

# Entities a Guest may call. Every other entity changes users or sessions and
# needs the "System Manager" role (the Keycloak listener's API user).
GUEST_ENTITIES = {"access_token"}

SYNC_ROLE = "System Manager"


@frappe.whitelist(allow_guest=True, methods=["POST"])
def api(**kwargs):
	"""
	Run one allow-listed action. The Keycloak event listener pushes user,
	role and session changes here in real time ("keycloak_events"), with the
	API key and secret of a System Manager. "access_token" is open to Guest.

	**Endpoint:** `/api/method/keycloak.keycloak_integration.api.v1.sdk.api`
	(the legacy path `/api/method/keycloak.sdk.api` is aliased to it in hooks.py)
	**HTTP Method:** POST
	**Parameters:**
		- version (str, required): API version. Only "v1" is supported.
		- entity (str, required): "keycloak_events" or "access_token".
		- method (str, required): "handle_event" or "get_access_token".
		- operation (str, keycloak_events): upsert_user / disable_user / logout_user.
		- user (dict, keycloak_events): {id, username, email, firstName, lastName, enabled}.
		- roles (list[str], optional): The user's client roles for this site.
		- usr / pwd (str, access_token): User name and password.
	**Response:**
	```json
	{"message": {"user": "jane@example.com", "operation": "upsert_user", "exec_time": "0.0123 seconds"}}
	{"message": {"msg": "success", "data": {"access_token": "token <key>:<secret>"}, "exec_time": "0.0123 seconds"}}
	```
	Unknown
	entities and methods respond with `{"message": {"msg": "error", "error": "..."}}`.
	"""
	started_at = time.monotonic()
	kwargs.pop("cmd", None)

	handler = HANDLERS.get((kwargs.get("version"), kwargs.get("entity"), kwargs.get("method")))
	if not handler:
		return error_response(_("Unsupported version, entity or method"))

	# Explicit check: frappe.only_for() is skipped in tests, and this guard must hold everywhere.
	if kwargs.get("entity") not in GUEST_ENTITIES and SYNC_ROLE not in frappe.get_roles():
		raise frappe.PermissionError(_("Not permitted"))

	response = handler(kwargs)
	if isinstance(response, dict):
		response["exec_time"] = f"{round(time.monotonic() - started_at, 4)} seconds"

	return response
