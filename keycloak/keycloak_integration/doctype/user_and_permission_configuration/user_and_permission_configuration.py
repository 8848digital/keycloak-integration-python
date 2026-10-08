# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.

from frappe.model.document import Document

from keycloak.keycloak_integration.doctype.user_and_permission_configuration.user_and_permission_configuration_utils import (
	delete_user_permission_records,
	sync_user_permissions,
	validate_permission_type_doctypes,
)


class UserandPermissionConfiguration(Document):
	"""Grants a user a set of User Permissions defined by a Permission Type."""

	def validate(self):
		"""
		Only allow DocTypes that the selected Permission Type contains.

		Returns:
		        None
		"""
		validate_permission_type_doctypes(self)

	def before_save(self):
		"""
		Create and delete User Permission records to match the rows.

		Returns:
		        None
		"""
		sync_user_permissions(self)

	def after_delete(self):
		"""
		Delete the User Permission records this configuration created.

		Returns:
		        None
		"""
		delete_user_permission_records(self)
