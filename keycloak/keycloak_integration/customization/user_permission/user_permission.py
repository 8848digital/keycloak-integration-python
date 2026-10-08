# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.

"""doc_events hooks for User Permission (owned by Frappe)."""

from keycloak.keycloak_integration.customization.user_permission.user_permission_utils import (
	validate_not_linked_to_configuration,
)


def on_trash(doc, method=None):
	"""
	Block deleting a User Permission that a configuration manages.

	Parameters:
		doc (Document, required): The User Permission.
		method (str, optional): The hook event name.

	Returns:
		None
	"""
	validate_not_linked_to_configuration(doc)
