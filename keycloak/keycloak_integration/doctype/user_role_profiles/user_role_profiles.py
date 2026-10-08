# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.

from frappe.model.document import Document


class UserRoleProfiles(Document):
	"""The Role Profiles a user received from Keycloak role mappings."""

	def validate(self):
		"""
		Drop duplicate Role Profile rows, keeping the first one.

		Returns:
		        None
		"""
		seen = set()
		unique_rows = []
		for row in self.role_profiles:
			if row.role_profile not in seen:
				seen.add(row.role_profile)
				unique_rows.append(row)

		for idx, row in enumerate(unique_rows, start=1):
			row.idx = idx

		self.set("role_profiles", unique_rows)
