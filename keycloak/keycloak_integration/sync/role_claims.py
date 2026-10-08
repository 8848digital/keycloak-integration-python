# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.

"""Apply the Role Profiles a user holds in Keycloak, read from the login claims."""

import frappe

USER_ROLE_PROFILES_DOCTYPE = "User Role Profiles"
ROLE_PROFILES_TABLE_DOCTYPE = "Role Profiles Table"
ROLE_PROFILE_MAPPING_DOCTYPE = "Erpnext Keycloak Role Profile Mapping"


def get_client_roles(userinfo, client_id):
	"""
	Read the user's roles for this site's client from the standard Keycloak
	claim "resource_access.<client_id>.roles". Keycloak puts effective roles
	there, so roles from groups and composite roles are included.

	Parameters:
		userinfo (dict, required): The userinfo / token claims.
		client_id (str, required): This site's Keycloak client id.

	Returns:
		list[str] | None: The role names, or None when the claim is missing
			(mapper not configured), so callers can leave roles untouched.
	"""
	resource_access = (userinfo or {}).get("resource_access")
	if not isinstance(resource_access, dict):
		return None

	return list((resource_access.get(client_id) or {}).get("roles") or [])


def sync_user_role_profiles(username, keycloak_roles):
	"""
	Make the user's Role Profiles match their Keycloak client roles, then
	rebuild the user's roles. Keycloak roles that are not Role Profiles
	(for example "uma_protection") are ignored. Users who never had a
	Keycloak-managed Role Profile and receive none are left alone, so
	manually managed users keep their roles.

	Parameters:
		username (str, required): The ERPNext User name.
		keycloak_roles (list[str], required): Client role names from Keycloak.

	Returns:
		list[str]: The Role Profiles now assigned.
	"""
	role_profiles = get_role_profiles_for(keycloak_roles)
	has_record = frappe.db.exists(USER_ROLE_PROFILES_DOCTYPE, username)
	if not role_profiles and not has_record:
		return []

	if has_record:
		record = frappe.get_doc(USER_ROLE_PROFILES_DOCTYPE, username)
	else:
		record = frappe.new_doc(USER_ROLE_PROFILES_DOCTYPE)
		record.user = username

	if sorted(row.role_profile for row in record.role_profiles) != role_profiles:
		record.set("role_profiles", [{"role_profile": name} for name in role_profiles])
		record.save(ignore_permissions=True)

	assign_collective_roles(username)
	return role_profiles


def get_role_profiles_for(keycloak_roles):
	"""
	Translate Keycloak role names to Role Profile names. A mapping record
	wins; otherwise a Role Profile with the same name is used.

	Parameters:
		keycloak_roles (list[str], required): Keycloak role names.

	Returns:
		list[str]: Sorted, unique Role Profile names.
	"""
	if not keycloak_roles:
		return []

	mapped = dict(
		frappe.get_all(
			ROLE_PROFILE_MAPPING_DOCTYPE,
			filters={"keycloak_realm_role_name": ["in", keycloak_roles]},
			fields=["keycloak_realm_role_name", "role_profile_name"],
			as_list=True,
		)
	)
	same_name = set(frappe.get_all("Role Profile", filters={"name": ["in", keycloak_roles]}, pluck="name"))
	return sorted({mapped.get(role) or role for role in keycloak_roles if role in mapped or role in same_name})


def assign_collective_roles(username):
	"""
	Replace the user's roles with the union of roles from every Role Profile
	in the user's "User Role Profiles" record. Skips the save when nothing
	changed, so logins do not rewrite the user every time.

	Parameters:
		username (str, required): The ERPNext User name.

	Returns:
		None
	"""
	role_profiles = frappe.get_all(
		ROLE_PROFILES_TABLE_DOCTYPE,
		filters={"parenttype": USER_ROLE_PROFILES_DOCTYPE, "parent": username},
		pluck="role_profile",
	)
	roles = set(
		frappe.get_all(
			"Has Role",
			filters={"parenttype": "Role Profile", "parent": ["in", role_profiles or [""]]},
			pluck="role",
		)
	)

	user = frappe.get_doc("User", username)
	if {row.role for row in user.roles} == roles and not user.role_profile_name:
		return

	user.set("roles", [])
	user.set("role_profile_name", None)
	for role in sorted(roles):
		user.append("roles", {"role": role})

	user.save(ignore_permissions=True)
