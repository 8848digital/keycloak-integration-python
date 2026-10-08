# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.

"""on_login hooks: apply Keycloak roles, then check the User Permission rule."""

import frappe

from keycloak.keycloak_integration.sync.role_claims import (
	get_client_roles,
	sync_user_role_profiles,
)
from keycloak.utils.keycloak_admin import KEYCLOAK_PROVIDER


def sync_roles_from_keycloak(login_manager):
	"""
	on_login hook: during a Keycloak login, give the user the Role Profiles
	that match their client roles in the token. Runs before Frappe creates
	the session, so a role change (which can change the user type) does not
	end the new session.

	Parameters:
	        login_manager (LoginManager, required): The login in progress.

	Returns:
	        None
	"""
	userinfo = frappe.flags.keycloak_userinfo
	if not userinfo or login_manager.user in ("Administrator", "Guest"):
		return

	client_id = frappe.db.get_value("Social Login Key", KEYCLOAK_PROVIDER, "client_id")
	keycloak_roles = get_client_roles(userinfo, client_id)
	if keycloak_roles is None:
		frappe.log_error(
			"Keycloak role sync skipped",
			f"No resource_access claim for client {client_id}; add the client-roles mapper to userinfo.",
		)
		return

	sync_user_role_profiles(login_manager.user, keycloak_roles)


def validate_user_permission(login_manager):
	"""
	on_login hook: reject the login when the user has no User Permission.
	Runs before Frappe creates the session, so a rejected login leaves no
	session behind. Administrator and the setup wizard are always allowed.

	Parameters:
	        login_manager (LoginManager, required): The login in progress.

	Returns:
	        None

	Raises:
	        frappe.AuthenticationError: When the user has no User Permission.
	"""
	user = login_manager.user
	if user == "Administrator" or frappe.flags.in_setup_wizard:
		return

	email = frappe.db.get_value("User", user, "email") or user
	if not frappe.db.exists("User Permission", {"user": email}):
		raise frappe.AuthenticationError
