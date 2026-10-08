# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.

"""Shared builders for the Keycloak Integration tests."""

import frappe

KEYCLOAK_ROOT_URL = "http://keycloak.test/"
KEYCLOAK_REALM = "erp"


def make_user(email, roles=None):
	"""
	Create (or return) a website-free System User for tests.

	Parameters:
		email (str, required): The user's email (also the User name).
		roles (list[str], optional): Roles to grant.

	Returns:
		Document: The User.
	"""
	if frappe.db.exists("User", email):
		return frappe.get_doc("User", email)

	user = frappe.get_doc(
		{"doctype": "User", "email": email, "first_name": email.split("@")[0], "send_welcome_email": 0}
	)
	for role in roles or []:
		user.append("roles", {"role": role})

	return user.insert(ignore_permissions=True)


def make_role_profile(name, roles):
	"""
	Create (or return) a Role Profile with the given roles.

	Parameters:
		name (str, required): The Role Profile name.
		roles (list[str], required): Roles in the profile.

	Returns:
		Document: The Role Profile.
	"""
	if frappe.db.exists("Role Profile", name):
		return frappe.get_doc("Role Profile", name)

	return frappe.get_doc(
		{"doctype": "Role Profile", "role_profile": name, "roles": [{"role": role} for role in roles]}
	).insert(ignore_permissions=True)


def make_keycloak_login_key(enabled=1):
	"""
	Create the "keycloak" Social Login Key used by the Admin API helpers.

	Parameters:
		enabled (int, optional): Value of the enable_keycloak custom field.

	Returns:
		Document: The Social Login Key.
	"""
	frappe.delete_doc("Social Login Key", "keycloak", ignore_missing=True, force=True)
	return frappe.get_doc(
		{
			"doctype": "Social Login Key",
			"provider_name": "Keycloak",
			"social_login_provider": "Custom",
			"enable_social_login": 0,
			"enable_keycloak": enabled,
			"client_id": "erp-client",
			"client_secret": "erp-secret",
			"root_url": KEYCLOAK_ROOT_URL,
			"realm_name": KEYCLOAK_REALM,
			"authorize_url": "/protocol/openid-connect/auth",
			"access_token_url": "/protocol/openid-connect/token",
			"redirect_url": "/api/method/frappe.integrations.oauth2_logins.custom/keycloak",
		}
	).insert(ignore_permissions=True)


class FakeResponse:
	"""Minimal stand-in for requests.Response."""

	def __init__(self, status_code=200, payload=None, text=""):
		"""
		Parameters:
			status_code (int, optional): HTTP status.
			payload (dict, optional): Value returned by json().
			text (str, optional): Body text.
		"""
		self.status_code = status_code
		self.payload = payload or {}
		self.text = text

	def json(self):
		"""
		Returns:
			dict: The JSON payload.
		"""
		return self.payload

	def raise_for_status(self):
		"""
		Raise like requests does for 4xx/5xx responses.

		Returns:
			None
		"""
		if self.status_code >= 400:
			raise Exception(f"HTTP {self.status_code}")
