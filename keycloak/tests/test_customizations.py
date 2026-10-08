# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.

"""Tests for the Role Profile, Social Login Key and User Permission hooks."""

from types import SimpleNamespace
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from keycloak.keycloak_integration.customization.role_profile import role_profile_utils
from keycloak.keycloak_integration.customization.social_login_key.social_login_key_utils import (
	set_missing_url,
)
from keycloak.tests.utils import FakeResponse, make_role_profile


class TestSocialLoginKeyUrls(FrappeTestCase):
	"""base_url and root_url/realm_name are derived from each other."""

	def test_base_url_from_root_and_realm(self):
		"""root_url + realm_name -> base_url."""
		doc = SimpleNamespace(name="keycloak", base_url=None, root_url="http://kc:8080/", realm_name="erp")
		set_missing_url(doc)
		self.assertEqual(doc.base_url, "http://kc:8080/realms/erp")

	def test_root_and_realm_from_base_url(self):
		"""base_url -> root_url + realm_name."""
		doc = SimpleNamespace(name="keycloak", base_url="http://kc:8080/realms/erp/", root_url=None, realm_name=None)
		set_missing_url(doc)
		self.assertEqual(doc.root_url, "http://kc:8080/")
		self.assertEqual(doc.realm_name, "erp")

	def test_other_providers_untouched(self):
		"""Only the "keycloak" key is changed."""
		doc = SimpleNamespace(name="google", base_url=None, root_url="http://x/", realm_name="r")
		set_missing_url(doc)
		self.assertIsNone(doc.base_url)


class TestRoleProfileHooks(FrappeTestCase):
	"""Role Profile changes are pushed to Keycloak."""

	def test_new_role_profile_creates_client_role(self):
		"""A new Role Profile becomes a client role of this site's client, and is mapped."""
		responses = [FakeResponse(201), FakeResponse(200, {"id": "role-uuid"})]
		with (
			patch.object(role_profile_utils, "get_keycloak_access_token", return_value="token"),
			patch.object(role_profile_utils, "get_site_client_uuid", return_value="client-uuid"),
			patch.object(role_profile_utils, "admin_request", side_effect=responses) as admin_request,
		):
			make_role_profile("KC Hook Profile", ["Sales User"])

		method, path, token = admin_request.call_args_list[0].args
		self.assertEqual((method, path, token), ("POST", "clients/client-uuid/roles", "token"))
		self.assertEqual(admin_request.call_args_list[0].kwargs["json"]["name"], "KC Hook Profile")
		mapping = frappe.get_doc("Erpnext Keycloak Role Profile Mapping", "KC Hook Profile")
		self.assertEqual((mapping.role_profile_id, mapping.keycloak_realm_role_name), ("role-uuid", "KC Hook Profile"))

	def test_keycloak_rejection_blocks_save(self):
		"""If Keycloak refuses the role, the Role Profile is not created."""
		with (
			patch.object(role_profile_utils, "get_keycloak_access_token", return_value="token"),
			patch.object(role_profile_utils, "get_site_client_uuid", return_value="client-uuid"),
			patch.object(role_profile_utils, "admin_request", return_value=FakeResponse(403, text="forbidden")),
			self.assertRaises(frappe.ValidationError),
		):
			make_role_profile("KC Rejected Profile", ["Sales User"])

		self.assertFalse(frappe.db.exists("Role Profile", "KC Rejected Profile"))

	def test_delete_uses_mapped_name_url_encoded(self):
		"""Delete targets the mapped Keycloak role name, URL-encoded."""
		make_role_profile("KC Delete Profile", ["Sales User"])
		frappe.get_doc(
			{
				"doctype": "Erpnext Keycloak Role Profile Mapping",
				"role_profile_name": "KC Delete Profile",
				"role_profile_id": "rid",
				"keycloak_realm_role_name": "site a/KC Delete Profile",
			}
		).insert(ignore_permissions=True)

		with (
			patch.object(role_profile_utils, "get_keycloak_access_token", return_value="token"),
			patch.object(role_profile_utils, "get_site_client_uuid", return_value="client-uuid"),
			patch.object(role_profile_utils, "admin_request", return_value=FakeResponse(204)) as admin_request,
		):
			frappe.delete_doc("Role Profile", "KC Delete Profile", ignore_permissions=True)

		admin_request.assert_called_once_with(
			"DELETE", "clients/client-uuid/roles/site%20a%2FKC%20Delete%20Profile", "token"
		)
		self.assertFalse(frappe.db.exists("Erpnext Keycloak Role Profile Mapping", "KC Delete Profile"))

	def test_unmapped_role_profile_can_be_deleted(self):
		"""A Role Profile that was never synced is deleted locally."""
		make_role_profile("KC Unmapped Profile", ["Sales User"])
		with (
			patch.object(role_profile_utils, "get_keycloak_access_token", return_value="token"),
			patch.object(role_profile_utils, "admin_request") as admin_request,
		):
			frappe.delete_doc("Role Profile", "KC Unmapped Profile", ignore_permissions=True)

		admin_request.assert_not_called()
