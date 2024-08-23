# Copyright (c) 2024, Amandeep and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class UserRoleProfiles(Document):
	def validate(self):
		unique_role_profiles = set()
		duplicate_row_to_remove = []
		for row in self.role_profiles:
			if row.role_profile in unique_role_profiles:
				duplicate_row_to_remove.append(row.role_profile)
			else:
				unique_role_profiles.add(row.role_profile)

		for role_profile in duplicate_row_to_remove:
			self.remove(role_profile)