# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.

"""Helpers that talk to the Keycloak Admin REST API on behalf of this site."""

from urllib.parse import quote

import frappe
import requests

KEYCLOAK_PROVIDER = "keycloak"

# Seconds. A hung Keycloak must never hang a Desk save or a logout request.
REQUEST_TIMEOUT = 15


def get_keycloak_settings():
	"""
	Return the enabled "keycloak" Social Login Key, or None when Keycloak
	sync is not configured or not enabled on this site.

	Returns:
		Document | None: The Social Login Key document.
	"""
	if not frappe.db.exists("Social Login Key", KEYCLOAK_PROVIDER):
		return None

	settings = frappe.get_cached_doc("Social Login Key", KEYCLOAK_PROVIDER)
	if not settings.get("enable_keycloak"):
		return None

	return settings


def get_keycloak_access_token():
	"""
	Fetch a service-account access token with the client-credentials grant.

	Returns:
		str | None: The bearer token, or None when Keycloak is not enabled.

	Raises:
		requests.HTTPError: When Keycloak rejects the client credentials.
	"""
	settings = get_keycloak_settings()
	if not settings:
		return None

	response = requests.post(
		join_url(settings.base_url, settings.access_token_url),
		data={
			"client_id": settings.client_id,
			"client_secret": settings.get_password("client_secret"),
			"grant_type": "client_credentials",
		},
		headers={"Content-Type": "application/x-www-form-urlencoded"},
		timeout=REQUEST_TIMEOUT,
	)
	response.raise_for_status()
	return response.json()["access_token"]


def get_admin_realm_url(settings=None):
	"""
	Build the Admin REST API base URL for the configured realm.

	Parameters:
		settings (Document, optional): The Social Login Key. Loaded when omitted.

	Returns:
		str: For example "https://sso.example.com/admin/realms/erp".
	"""
	settings = settings or frappe.get_cached_doc("Social Login Key", KEYCLOAK_PROVIDER)
	if settings.get("root_url") and settings.get("realm_name"):
		return join_url(settings.root_url, "admin/realms", quote(settings.realm_name, safe=""))

	# base_url has the shape "<root>/realms/<realm>".
	return settings.base_url.rstrip("/").replace("/realms/", "/admin/realms/", 1)


def admin_request(method, path, access_token, **kwargs):
	"""
	Call one Admin REST API endpoint of the configured realm.

	Parameters:
		method (str, required): HTTP method, for example "POST".
		path (str, required): Path below the realm, for example "roles".
		access_token (str, required): Bearer token from get_keycloak_access_token.
		**kwargs: Passed to requests.request (json, params, ...).

	Returns:
		requests.Response: The raw response; callers check the status code.
	"""
	return requests.request(
		method,
		join_url(get_admin_realm_url(), path),
		headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
		timeout=REQUEST_TIMEOUT,
		**kwargs,
	)


def get_site_client_uuid(access_token, settings=None):
	"""
	Find the internal id of this site's Keycloak client (the Social Login
	Key's Client ID). Role Profiles are kept as client roles of that client,
	so every ERPNext site has its own set of roles in one realm.

	Parameters:
		access_token (str, required): Bearer token from get_keycloak_access_token.
		settings (Document, optional): The Social Login Key. Loaded when omitted.

	Returns:
		str: The client's internal id (UUID).

	Raises:
		frappe.ValidationError: When Keycloak has no such client.
	"""
	settings = settings or frappe.get_cached_doc("Social Login Key", KEYCLOAK_PROVIDER)
	response = admin_request("GET", "clients", access_token, params={"clientId": settings.client_id})
	response.raise_for_status()
	clients = response.json()
	if not clients:
		frappe.throw(frappe._("Keycloak client {0} not found").format(settings.client_id))

	return clients[0]["id"]


def join_url(*parts):
	"""
	Join URL parts with exactly one slash between them.

	Parameters:
		*parts (str): URL fragments, for example ("https://kc/", "/realms").

	Returns:
		str: The joined URL, for example "https://kc/realms".
	"""
	cleaned = [str(part).strip("/") for part in parts if part]
	return "/".join(cleaned)


def quote_path(segment):
	"""
	Percent-encode one URL path segment, including "/".

	Parameters:
		segment (str, required): A role name, session id, etc.

	Returns:
		str: The encoded segment.
	"""
	return quote(str(segment), safe="")
