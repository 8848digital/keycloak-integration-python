# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.

"""End the Keycloak SSO session when the user logs out of ERPNext."""

import frappe
from frappe import _

from keycloak.utils.keycloak_admin import (
	KEYCLOAK_PROVIDER,
	admin_request,
	get_keycloak_access_token,
	quote_path,
)

# Matches Frappe's longest session expiry, so the entry outlives the session.
SSO_SESSION_TTL = 60 * 60 * 24 * 30


def remember_sso_session(provider, session_state):
	"""
	Store the identity provider's session id for the current Frappe session.
	It is kept server side (not in a cookie), so a client cannot change it.

	Parameters:
		provider (str, required): The Social Login Key name.
		session_state (str, required): The provider's session id.

	Returns:
		None
	"""
	sid = frappe.session.sid
	if not sid or frappe.session.user == "Guest":
		return

	frappe.cache.set_value(
		__cache_key(sid),
		{"provider": provider, "session_state": session_state},
		expires_in_sec=SSO_SESSION_TTL,
	)


def logout(login_manager=None):
	"""
	on_logout hook: delete the user's Keycloak session, when this Frappe
	session was opened through Keycloak.

	Parameters:
		login_manager (LoginManager, optional): Passed by Frappe; unused.

	Returns:
		None
	"""
	sid = frappe.session.sid
	sso_session = frappe.cache.get_value(__cache_key(sid)) if sid else None
	if not sso_session or sso_session.get("provider") != KEYCLOAK_PROVIDER:
		return

	frappe.cache.delete_value(__cache_key(sid))
	delete_keycloak_session(sso_session["session_state"])


def delete_keycloak_session(session_state, notify=True):
	"""
	Delete one Keycloak user session through the Admin REST API. Failures
	are logged (and reported when notify is set), but never block the caller.

	Parameters:
		session_state (str, required): The Keycloak session id.
		notify (bool, optional): Show a message to the user. Default True.

	Returns:
		bool: True when Keycloak confirmed the deletion.
	"""
	provider_name = frappe.db.get_value("Social Login Key", KEYCLOAK_PROVIDER, "provider_name")
	try:
		access_token = get_keycloak_access_token()
		response = admin_request("DELETE", f"sessions/{quote_path(session_state)}", access_token)
	except Exception:
		frappe.log_error("SSO Logout Error")
		__notify(notify, _("Logout from {0} failed").format(provider_name))
		return False

	if response.status_code == 204:
		__notify(notify, _("Logged out successfully from {0}").format(provider_name))
		return True

	frappe.log_error(
		"SSO Logout Error",
		{"status_code": response.status_code, "response": response.text, "session_state": session_state},
	)
	__notify(notify, _("Logout from {0} failed").format(provider_name))
	return False


def __notify(enabled, message):
	"""
	Show a message to the user when enabled.

	Parameters:
		enabled (bool, required): Whether to show it.
		message (str, required): The translated message.

	Returns:
		None
	"""
	if enabled:
		frappe.msgprint(message)


def __cache_key(sid):
	"""
	Build the cache key for a Frappe session id.

	Parameters:
		sid (str, required): The Frappe session id.

	Returns:
		str: The cache key.
	"""
	return f"keycloak_sso_session:{sid}"
