# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.

import frappe
from frappe.tests.utils import FrappeTestCase


class TestPermissionType(FrappeTestCase):
	"""Each DocType may appear only once in a Permission Type."""

	def test_duplicate_doctype_rejected(self):
		"""Two rows for the same DocType fail validation."""
		doc = frappe.get_doc(
			{
				"doctype": "Permission Type",
				"name1": "KC Duplicate Type",
				"permission_type_doctype": [{"allow_doctype": "Company"}, {"allow_doctype": "Company"}],
			}
		)
		with self.assertRaises(frappe.ValidationError):
			doc.insert(ignore_permissions=True)

	def test_unique_doctypes_saved(self):
		"""Distinct DocTypes save fine."""
		doc = frappe.get_doc(
			{
				"doctype": "Permission Type",
				"name1": "KC Unique Type",
				"permission_type_doctype": [{"allow_doctype": "Company"}, {"allow_doctype": "Cost Center"}],
			}
		).insert(ignore_permissions=True)
		self.assertEqual(len(doc.permission_type_doctype), 2)

	def test_applicable_for_needs_apply_to_all_off(self):
		"""Apply To All Doctypes (default 1) plus Applicable For is contradictory."""
		doc = frappe.get_doc(
			{
				"doctype": "Permission Type",
				"name1": "KC Contradictory Type",
				"permission_type_doctype": [{"allow_doctype": "Customer", "applicable_for": "Sales Order"}],
			}
		)
		with self.assertRaises(frappe.ValidationError):
			doc.insert(ignore_permissions=True)

		doc.permission_type_doctype[0].apply_to_all_doctypes = 0
		doc.insert(ignore_permissions=True)

	def test_hide_descendants_only_for_tree_doctypes(self):
		"""Hide Descendants is rejected for a non-tree DocType."""
		doc = frappe.get_doc(
			{
				"doctype": "Permission Type",
				"name1": "KC Hide Flat Type",
				"permission_type_doctype": [{"allow_doctype": "Customer", "hide_descendants": 1}],
			}
		)
		with self.assertRaises(frappe.ValidationError):
			doc.insert(ignore_permissions=True)
