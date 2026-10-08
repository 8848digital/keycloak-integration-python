# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.

"""Tests for real-time events pushed by the Keycloak listener."""

from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from keycloak.keycloak_integration.api.v1.sdk import api
from keycloak.keycloak_integration.sync import keycloak_events
from keycloak.keycloak_integration.sync.keycloak_events import find_user, handle_event
from keycloak.tests.utils import make_role_profile

EMAIL = "kc-event-user@example.com"
KEYCLOAK_ID = "kc-event-sub-1"
PROFILE = "KC Event Profile"


def kc_user(**fields):
	"""
	Build a Keycloak user as the listener sends it.

	Parameters:
	        **fields: Fields to override.

	Returns:
	        dict: The Keycloak user.
	"""
	return {
		"id": KEYCLOAK_ID,
		"username": "kc-event",
		"email": EMAIL,
		"firstName": "Kay",
		"lastName": "Event",
		"enabled": True,
		**fields,
	}


class TestKeycloakEvents(FrappeTestCase):
	"""Users, roles and sessions follow Keycloak in real time."""

	@classmethod
	def setUpClass(cls):
		"""
		Create a Role Profile used as a Keycloak client role.

		Returns:
		        None
		"""
		super().setUpClass()
		make_role_profile(PROFILE, ["Sales User", "Stock User"])

	def tearDown(self):
		"""
		Restore the Administrator session.

		Returns:
		        None
		"""
		frappe.set_user("Administrator")

	def test_upsert_creates_linked_user_with_roles(self):
		"""upsert_user creates the user, links it by Keycloak id and applies roles."""
		result = handle_event({"operation": "upsert_user", "user": kc_user(), "roles": [PROFILE]})
		self.assertEqual(result["user"], EMAIL)

		user = frappe.get_doc("User", EMAIL)
		self.assertEqual(user.get_social_login_userid("keycloak"), KEYCLOAK_ID)
		self.assertTrue({"Sales User", "Stock User"} <= set(frappe.get_roles(EMAIL)))
		self.assertEqual(find_user({"id": KEYCLOAK_ID}), EMAIL)

	def test_upsert_updates_and_removes_roles(self):
		"""A later upsert updates the name and drops roles no longer held."""
		handle_event({"operation": "upsert_user", "user": kc_user(), "roles": [PROFILE]})
		handle_event({"operation": "upsert_user", "user": kc_user(firstName="Kai"), "roles": []})

		frappe.clear_cache(user=EMAIL)
		self.assertEqual(frappe.db.get_value("User", EMAIL, "first_name"), "Kai")
		self.assertNotIn("Stock User", frappe.get_roles(EMAIL))

	def test_upsert_without_roles_keeps_roles(self):
		"""An event without "roles" (e.g. profile edit) leaves roles alone."""
		handle_event({"operation": "upsert_user", "user": kc_user(), "roles": [PROFILE]})
		handle_event({"operation": "upsert_user", "user": kc_user(lastName="Changed")})
		self.assertIn("Sales User", frappe.get_roles(EMAIL))

	def test_disable_and_logout_end_sessions(self):
		"""disable_user disables and ends sessions; logout_user only ends sessions."""
		handle_event({"operation": "upsert_user", "user": kc_user()})
		with patch.object(keycloak_events, "clear_sessions") as clear_sessions:
			handle_event({"operation": "logout_user", "user": {"id": KEYCLOAK_ID}})
			handle_event({"operation": "disable_user", "user": {"id": KEYCLOAK_ID}})

		self.assertEqual(clear_sessions.call_count, 2)
		self.assertEqual(frappe.db.get_value("User", EMAIL, "enabled"), 0)

		handle_event({"operation": "upsert_user", "user": kc_user(enabled=True)})
		self.assertEqual(frappe.db.get_value("User", EMAIL, "enabled"), 1)

	def test_unknown_user_events_are_noops(self):
		"""Logout / disable of a user ERPNext never saw does nothing."""
		self.assertIsNone(handle_event({"operation": "logout_user", "user": {"id": "nobody"}})["user"])
		self.assertIsNone(handle_event({"operation": "disable_user", "user": {"id": "nobody"}})["user"])

	def test_bad_events_are_rejected(self):
		"""Unknown operations and missing user ids fail validation."""
		with self.assertRaises(frappe.ValidationError):
			handle_event({"operation": "drop_user", "user": kc_user()})
		with self.assertRaises(frappe.ValidationError):
			handle_event({"operation": "upsert_user", "user": {"email": EMAIL}})

	def test_endpoint_requires_system_manager(self):
		"""Guests cannot push events through the API."""
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			api(
				version="v1",
				entity="keycloak_events",
				method="handle_event",
				operation="upsert_user",
				user=kc_user(),
			)
