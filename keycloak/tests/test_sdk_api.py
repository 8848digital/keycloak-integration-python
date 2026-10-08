# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.

"""Security and routing tests for the Keycloak sync entry point."""

import frappe
from frappe.tests.utils import FrappeTestCase

from keycloak.keycloak_integration.api.v1.sdk import api
from keycloak.tests.utils import make_user

SYNC_EMAIL = "kc-sync-target@example.com"


class TestSdkApi(FrappeTestCase):
	"""The endpoint must only route allow-listed actions, for allowed users."""

	def tearDown(self):
		"""
		Restore the Administrator session after each test.

		Returns:
		        None
		"""
		frappe.set_user("Administrator")

	def test_retired_sync_entities_are_refused(self):
		"""User/role sync moved to the standard login; the old entities are gone."""
		frappe.set_user("Guest")
		with self.assertRaises(frappe.ValidationError):
			api(**self.__user_payload("create"))
		frappe.set_user("Administrator")
		self.assertFalse(frappe.db.exists("User", SYNC_EMAIL))

	def test_unknown_method_is_not_executed(self):
		"""The old eval() dispatch ran attacker-chosen code; now it is refused."""
		with self.assertRaises(frappe.ValidationError):
			api(
				version="v1",
				entity="map_users",
				method="map_users_in_frappe(None) or frappe.db.sql('select 1')",
			)

	def test_unknown_version_is_refused(self):
		"""Version "v2" used to raise NameError; now it is a clean error."""
		with self.assertRaises(frappe.ValidationError):
			api(version="v2", entity="map_users", method="map_users_in_frappe")

	def test_guest_access_token_wrong_password(self):
		"""Guest may call access_token, but wrong passwords get a generic error."""
		make_user("kc-token-user@example.com")
		frappe.set_user("Guest")
		response = api(
			version="v1",
			entity="access_token",
			method="get_access_token",
			usr="kc-token-user@example.com",
			pwd="wrong",
		)
		self.assertEqual(response["msg"], "error")
		self.assertIn("exec_time", response)

	def test_legacy_path_is_aliased(self):
		"""Deployed listeners still call keycloak.sdk.api."""
		self.assertEqual(
			frappe.override_whitelisted_method("keycloak.sdk.api"),
			"keycloak.keycloak_integration.api.v1.sdk.api",
		)

	@staticmethod
	def __user_payload(operation):
		"""
		Build a map_users payload like the Keycloak listener sends.

		Parameters:
		        operation (str, required): create / update / delete.

		Returns:
		        dict: The request parameters.
		"""
		return {
			"version": "v1",
			"entity": "map_users",
			"method": "map_users_in_frappe",
			"operation": operation,
			"id": "kc-id-sdk",
			"email": SYNC_EMAIL,
			"userName": "kc-sync-target",
			"firstName": "Sync",
			"lastName": "null",
		}
