# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.

import frappe
from frappe.tests.utils import FrappeTestCase

from keycloak.tests.utils import make_role_profile


class TestUserRoleProfiles(FrappeTestCase):
	"""Duplicate Role Profile rows are dropped on save."""

	def test_duplicates_removed(self):
		"""The old validate crashed on duplicates; now they are de-duplicated."""
		make_role_profile("KC URP Profile", ["Sales User"])
		doc = frappe.get_doc(
			{
				"doctype": "User Role Profiles",
				"user": "kc-urp@example.com",
				"role_profiles": [{"role_profile": "KC URP Profile"}, {"role_profile": "KC URP Profile"}],
			}
		).insert(ignore_permissions=True)
		self.assertEqual([row.role_profile for row in doc.role_profiles], ["KC URP Profile"])
		self.assertEqual(doc.role_profiles[0].idx, 1)
