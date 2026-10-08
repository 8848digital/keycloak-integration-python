# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.

from frappe.model.document import Document

from keycloak.keycloak_integration.doctype.permission_type.permission_type_utils import (
	validate_doctype_links,
	validate_row_options,
	validate_unique_doctypes,
)


class PermissionType(Document):
	"""A named set of DocTypes that a User and Permission Configuration can restrict."""

	def validate(self):
		"""
		Reject duplicate DocType rows, contradictory row options, and changes to rows that a
		configuration already uses.

		Returns:
		        None
		"""
		validate_unique_doctypes(self)
		validate_row_options(self)
		validate_doctype_links(self)
