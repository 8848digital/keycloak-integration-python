# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.

"""doc_events hooks for Social Login Key (owned by Frappe)."""

from keycloak.keycloak_integration.customization.social_login_key.social_login_key_utils import (
	set_missing_url,
)


def before_validate(doc, method=None):
	"""
	Fill in base_url, root_url and realm_name from each other.

	Parameters:
		doc (Document, required): The Social Login Key.
		method (str, optional): The hook event name.

	Returns:
		None
	"""
	set_missing_url(doc)
