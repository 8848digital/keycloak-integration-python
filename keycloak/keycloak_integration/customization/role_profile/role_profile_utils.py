# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.

"""Keep this site's Keycloak client roles and users' roles in step with Role Profiles."""

import frappe
from frappe import _

from keycloak.keycloak_integration.sync.role_claims import (
	ROLE_PROFILE_MAPPING_DOCTYPE,
	ROLE_PROFILES_TABLE_DOCTYPE,
	USER_ROLE_PROFILES_DOCTYPE,
	assign_collective_roles,
)
from keycloak.utils.keycloak_admin import (
	admin_request,
	get_keycloak_access_token,
	get_site_client_uuid,
	quote_path,
)


def create_role_profile_in_keycloak(doc):
	"""
	Create a client role, named like the Role Profile, on this site's
	Keycloak client, and record the mapping. Admins then grant it to users
	or groups in Keycloak as usual. A Keycloak error blocks the save.

	Parameters:
	        doc (Document, required): The Role Profile.

	Returns:
	        None
	"""
	if not doc.is_new():
		return

	access_token = get_keycloak_access_token()
	if not access_token:
		return

	roles_path = f"clients/{get_site_client_uuid(access_token)}/roles"
	role = {
		"name": doc.role_profile,
		"description": _("ERPNext Role Profile {0}").format(doc.role_profile),
	}
	response = admin_request("POST", roles_path, access_token, json=role)
	if response.status_code not in (201, 409):
		frappe.throw(_("Keycloak rejected the role: {0}").format(response.text))

	created = admin_request("GET", f"{roles_path}/{quote_path(doc.role_profile)}", access_token)
	role_id = created.json().get("id") if created.status_code == 200 else None
	__upsert_mapping(doc.role_profile, role_id)
	frappe.msgprint(_("Role Profile added successfully."))


def delete_role_profile_in_keycloak(doc):
	"""
	Delete the client role mapped to this Role Profile, then the mapping.
	A Role Profile with no mapping (never synced) is deleted locally only.

	Parameters:
	        doc (Document, required): The Role Profile.

	Returns:
	        None
	"""
	access_token = get_keycloak_access_token()
	if not access_token:
		return

	keycloak_role_name = frappe.db.get_value(
		ROLE_PROFILE_MAPPING_DOCTYPE, doc.role_profile, "keycloak_realm_role_name"
	)
	if not keycloak_role_name:
		return

	roles_path = f"clients/{get_site_client_uuid(access_token)}/roles"
	response = admin_request("DELETE", f"{roles_path}/{quote_path(keycloak_role_name)}", access_token)
	if response.status_code not in (204, 404):
		frappe.throw(_("Keycloak could not delete the role: {0}").format(response.text))

	frappe.msgprint(_("Role deleted successfully."))
	frappe.delete_doc(ROLE_PROFILE_MAPPING_DOCTYPE, doc.role_profile, ignore_permissions=True)


def queue_user_role_refresh(doc):
	"""
	After a Role Profile changes, rebuild the roles of every user that has
	it. Queued after commit, so the job reads the saved roles.

	Parameters:
	        doc (Document, required): The Role Profile.

	Returns:
	        None
	"""
	if doc.is_new():
		return

	usernames = frappe.get_all(
		ROLE_PROFILES_TABLE_DOCTYPE,
		filters={"parenttype": USER_ROLE_PROFILES_DOCTYPE, "role_profile": doc.role_profile},
		pluck="parent",
		distinct=True,
	)
	if usernames:
		frappe.enqueue(refresh_user_roles, usernames=usernames, enqueue_after_commit=True)


def refresh_user_roles(usernames):
	"""
	Background job: rebuild each user's roles from their Role Profiles. One
	failing user is logged and does not stop the others.

	Parameters:
	        usernames (list[str], required): ERPNext User names.

	Returns:
	        None
	"""
	for username in usernames:
		try:
			assign_collective_roles(username)
		except Exception:
			frappe.log_error(f"Role refresh failed for {username}")


def __upsert_mapping(role_profile, role_id):
	"""
	Record the Keycloak role of a Role Profile.

	Parameters:
	        role_profile (str, required): The Role Profile name (also the role name).
	        role_id (str, optional): The Keycloak role id.

	Returns:
	        None
	"""
	values = {"role_profile_id": role_id, "keycloak_realm_role_name": role_profile}
	if frappe.db.exists(ROLE_PROFILE_MAPPING_DOCTYPE, role_profile):
		frappe.db.set_value(ROLE_PROFILE_MAPPING_DOCTYPE, role_profile, values)
		return

	frappe.get_doc(
		{"doctype": ROLE_PROFILE_MAPPING_DOCTYPE, "role_profile_name": role_profile, **values}
	).insert(ignore_permissions=True)
