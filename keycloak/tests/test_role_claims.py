# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.

"""Tests for role sync from the standard Keycloak login claims."""

from types import SimpleNamespace
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from keycloak.keycloak_integration.login import sync_roles_from_keycloak
from keycloak.keycloak_integration.sync.role_claims import (
	get_client_roles,
	get_role_profiles_for,
	sync_user_role_profiles,
)
from keycloak.tests.utils import make_keycloak_login_key, make_role_profile, make_user

EMAIL = "kc-claims-user@example.com"
SALES = "KC Claims Sales"
STOCK = "KC Claims Stock"


class TestRoleClaims(FrappeTestCase):
	"""Keycloak client roles in the token decide the user's Role Profiles."""

	@classmethod
	def setUpClass(cls):
		"""
		Create a user and two Role Profiles sharing one role.

		Returns:
		        None
		"""
		super().setUpClass()
		make_user(EMAIL)
		make_role_profile(SALES, ["Sales User", "Accounts User"])
		make_role_profile(STOCK, ["Stock User", "Accounts User"])

	def test_get_client_roles(self):
		"""Roles come from resource_access.<client>.roles; missing claim gives None."""
		claims = {"resource_access": {"erp-client": {"roles": [SALES]}, "other": {"roles": ["x"]}}}
		self.assertEqual(get_client_roles(claims, "erp-client"), [SALES])
		self.assertEqual(get_client_roles(claims, "absent-client"), [])
		self.assertIsNone(get_client_roles({"email": "a@b.c"}, "erp-client"))

	def test_unknown_roles_are_ignored(self):
		"""Keycloak roles without a Role Profile (e.g. uma_protection) are skipped."""
		self.assertEqual(get_role_profiles_for([SALES, "uma_protection"]), [SALES])

	def test_sync_adds_and_removes_profiles(self):
		"""Roles follow Keycloak: add both, then drop one; shared roles stay."""
		sync_user_role_profiles(EMAIL, [SALES, STOCK])
		self.assertTrue({"Sales User", "Stock User", "Accounts User"} <= set(frappe.get_roles(EMAIL)))

		sync_user_role_profiles(EMAIL, [SALES])
		frappe.clear_cache(user=EMAIL)
		roles = set(frappe.get_roles(EMAIL))
		self.assertNotIn("Stock User", roles)
		self.assertTrue({"Sales User", "Accounts User"} <= roles)

		sync_user_role_profiles(EMAIL, [])
		frappe.clear_cache(user=EMAIL)
		self.assertNotIn("Sales User", frappe.get_roles(EMAIL))

	def test_manual_user_is_left_alone(self):
		"""A user never managed by Keycloak keeps manual roles when no profile matches."""
		user = make_user("kc-manual-user@example.com", roles=["Sales User"])
		self.assertEqual(sync_user_role_profiles(user.name, ["uma_protection"]), [])
		self.assertIn("Sales User", frappe.get_roles(user.name))

	def test_login_hook_uses_site_client(self):
		"""The on_login hook reads the claim of the Social Login Key's client."""
		make_keycloak_login_key()
		frappe.flags.keycloak_userinfo = {"resource_access": {"erp-client": {"roles": [STOCK]}}}
		try:
			sync_roles_from_keycloak(SimpleNamespace(user=EMAIL))
		finally:
			frappe.flags.keycloak_userinfo = None
			frappe.delete_doc("Social Login Key", "keycloak", ignore_missing=True, force=True)

		self.assertEqual(
			frappe.get_all("Role Profiles Table", filters={"parent": EMAIL}, pluck="role_profile"), [STOCK]
		)

	def test_login_hook_without_claim_keeps_roles(self):
		"""No resource_access claim (mapper missing): roles stay as they are."""
		sync_user_role_profiles(EMAIL, [SALES])
		frappe.flags.keycloak_userinfo = {"email": EMAIL}
		try:
			with patch("frappe.log_error") as log_error:
				sync_roles_from_keycloak(SimpleNamespace(user=EMAIL))
		finally:
			frappe.flags.keycloak_userinfo = None

		log_error.assert_called_once()
		self.assertIn("Sales User", frappe.get_roles(EMAIL))
