# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.

"""Apply real-time user, role and session changes pushed by the Keycloak listener."""

import frappe
from frappe import _
from frappe.sessions import clear_sessions

from keycloak.keycloak_integration.sync.role_claims import sync_user_role_profiles
from keycloak.utils.keycloak_admin import KEYCLOAK_PROVIDER


def handle_event(payload):
	"""
	Route one pushed Keycloak change to its handler.

	Parameters:
	        payload (dict, required): "operation" is upsert_user, disable_user or
	                logout_user; "user" is the Keycloak user ({id, username, email,
	                firstName, lastName, enabled}); "roles" (optional) are the user's
	                client roles for this site.

	Returns:
	        dict: {"user": <ERPNext user name or None>, "operation": <operation>}
	"""
	handlers = {"upsert_user": upsert_user, "disable_user": disable_user, "logout_user": logout_user}
	operation = payload.get("operation")
	handler = handlers.get(operation)
	if not handler:
		frappe.throw(_("Unsupported Keycloak event: {0}").format(operation))

	return {"user": handler(__parse_user(payload), payload), "operation": operation}


def upsert_user(keycloak_user, payload):
	"""
	Create or update the ERPNext user, link it to Keycloak the standard way
	(User Social Login, provider "keycloak", user id = Keycloak "sub"), and
	apply the client roles when the event carries them. A disabled Keycloak
	user is disabled here too and loses open sessions.

	Parameters:
	        keycloak_user (dict, required): The Keycloak user.
	        payload (dict, required): The event; may hold "roles".

	Returns:
	        str: The ERPNext user name.
	"""
	username = find_user(keycloak_user)
	email = keycloak_user.get("email")
	if not username and not email:
		frappe.throw(_("Keycloak user {0} has no e-mail").format(keycloak_user.get("username")))

	user = frappe.get_doc("User", username) if username else frappe.new_doc("User")
	if user.is_new():
		user.email = email
		user.send_welcome_email = 0

	user.first_name = (
		keycloak_user.get("firstName") or user.first_name or keycloak_user.get("username") or email
	)
	user.last_name = keycloak_user.get("lastName") or None
	user.enabled = 1 if keycloak_user.get("enabled", True) else 0
	if not user.get_social_login_userid(KEYCLOAK_PROVIDER):
		user.set_social_login_userid(
			KEYCLOAK_PROVIDER, userid=keycloak_user.get("id"), username=keycloak_user.get("username")
		)
	user.save(ignore_permissions=True)

	if payload.get("roles") is not None:
		sync_user_role_profiles(user.name, list(payload["roles"]))

	if not user.enabled:
		clear_sessions(user=user.name, force=True)

	return user.name


def disable_user(keycloak_user, payload=None):
	"""
	Disable the ERPNext user and end all of the user's ERPNext sessions.
	The user record and its history are kept.

	Parameters:
	        keycloak_user (dict, required): The Keycloak user (at least "id").
	        payload (dict, optional): The event; unused.

	Returns:
	        str | None: The ERPNext user name, or None when unknown.
	"""
	username = find_user(keycloak_user)
	if not username:
		return None

	frappe.db.set_value("User", username, "enabled", 0)
	clear_sessions(user=username, force=True)
	return username


def logout_user(keycloak_user, payload=None):
	"""
	End all ERPNext sessions of the user (Keycloak single logout).

	Parameters:
	        keycloak_user (dict, required): The Keycloak user (at least "id").
	        payload (dict, optional): The event; unused.

	Returns:
	        str | None: The ERPNext user name, or None when unknown.
	"""
	username = find_user(keycloak_user)
	if username:
		clear_sessions(user=username, force=True)

	return username


def find_user(keycloak_user):
	"""
	Find the ERPNext user for a Keycloak user: first by the standard social
	login link (Keycloak id), then by e-mail.

	Parameters:
	        keycloak_user (dict, required): {id, email, ...}.

	Returns:
	        str | None: The User name.
	"""
	keycloak_id = keycloak_user.get("id")
	if keycloak_id:
		linked = frappe.db.get_value(
			"User Social Login", {"provider": KEYCLOAK_PROVIDER, "userid": keycloak_id}, "parent"
		)
		if linked:
			return linked

	email = (keycloak_user.get("email") or "").lower()
	return frappe.db.get_value("User", {"email": email}, "name") if email else None


def __parse_user(payload):
	"""
	Return the "user" object of the event, parsed when sent as text.

	Parameters:
	        payload (dict, required): The event.

	Returns:
	        dict: The Keycloak user.
	"""
	keycloak_user = payload.get("user")
	if isinstance(keycloak_user, str):
		keycloak_user = frappe.parse_json(keycloak_user)

	if not isinstance(keycloak_user, dict) or not keycloak_user.get("id"):
		frappe.throw(_("Missing mandatory parameter: {0}").format("user.id"))

	return keycloak_user
