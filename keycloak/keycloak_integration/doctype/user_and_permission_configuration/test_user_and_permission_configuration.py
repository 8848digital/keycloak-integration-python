# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.

import frappe
from frappe.tests.utils import FrappeTestCase

from keycloak.keycloak_integration.api.v1.user_and_permission_configuration import (
	filter_doctypes_based_on_permissions,
)
from keycloak.tests.utils import make_user

USER = "kc-upc-user@example.com"
PERMISSION_TYPE = "KC UPC Type"


class TestUserandPermissionConfiguration(FrappeTestCase):
	"""A configuration creates and removes the User Permissions it owns."""

	@classmethod
	def setUpClass(cls):
		"""
		Create the user and a Permission Type for Company.

		Returns:
			None
		"""
		super().setUpClass()
		make_user(USER)
		if not frappe.db.exists("Permission Type", PERMISSION_TYPE):
			frappe.get_doc(
				{
					"doctype": "Permission Type",
					"name1": PERMISSION_TYPE,
					"permission_type_doctype": [{"allow_doctype": "Company", "apply_to_all_doctypes": 1}],
				}
			).insert(ignore_permissions=True)
		cls.company = frappe.get_all("Company", pluck="name", limit=1)[0]

	def test_lifecycle(self):
		"""Save creates the User Permission; it is protected; delete removes it."""
		config = frappe.get_doc(
			{
				"doctype": "User and Permission Configuration",
				"user": USER,
				"permission_type": PERMISSION_TYPE,
				"user_permission_doctype_value": [{"doc_type": "Company", "for_value": self.company}],
			}
		).insert(ignore_permissions=True)

		record = config.user_permission_doctype_value[0].user_permission_record
		self.assertTrue(frappe.db.exists("User Permission", {"name": record, "user": USER, "allow": "Company"}))

		# Deleting the managed User Permission directly is blocked.
		with self.assertRaises(frappe.ValidationError):
			frappe.delete_doc("User Permission", record, ignore_permissions=True)

		config.delete(ignore_permissions=True)
		self.assertFalse(frappe.db.exists("User Permission", record))

	def test_rejects_doctype_outside_permission_type(self):
		"""Rows may only use DocTypes of the Permission Type."""
		config = frappe.get_doc(
			{
				"doctype": "User and Permission Configuration",
				"user": USER,
				"permission_type": PERMISSION_TYPE,
				"user_permission_doctype_value": [{"doc_type": "Customer", "for_value": "x"}],
			}
		)
		with self.assertRaises(frappe.ValidationError):
			config.insert(ignore_permissions=True)

	def test_user_permission_guard_is_injection_safe(self):
		"""A quote in the name used to break the raw SQL; now it is a bound value."""
		from keycloak.keycloak_integration.customization.user_permission.user_permission_utils import (
			validate_not_linked_to_configuration,
		)

		doc = frappe._dict(name="x' OR '1'='1", flags=frappe._dict())
		validate_not_linked_to_configuration(doc)

	def test_search_query_filters_by_text(self):
		"""The link search returns the Permission Type's DocTypes matching the text."""
		args = ("DocType", "Comp", "name", 0, 20, {"permission_type": PERMISSION_TYPE})
		self.assertEqual(filter_doctypes_based_on_permissions(*args), (("Company",),))
		args = ("DocType", "zzz", "name", 0, 20, {"permission_type": PERMISSION_TYPE})
		self.assertEqual(filter_doctypes_based_on_permissions(*args), ())
