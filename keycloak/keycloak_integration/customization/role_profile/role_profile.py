# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.

"""doc_events hooks for Role Profile (owned by Frappe)."""

from keycloak.keycloak_integration.customization.role_profile.role_profile_utils import (
	create_role_profile_in_keycloak,
	delete_role_profile_in_keycloak,
	queue_user_role_refresh,
)


def before_validate(doc, method=None):
	"""
	Queue a role refresh for every user holding this Role Profile.

	Parameters:
		doc (Document, required): The Role Profile.
		method (str, optional): The hook event name.

	Returns:
		None
	"""
	queue_user_role_refresh(doc)


def validate(doc, method=None):
	"""
	Create the matching realm role in Keycloak for a new Role Profile.

	Parameters:
		doc (Document, required): The Role Profile.
		method (str, optional): The hook event name.

	Returns:
		None
	"""
	create_role_profile_in_keycloak(doc)


def on_trash(doc, method=None):
	"""
	Delete the matching realm role from Keycloak.

	Parameters:
		doc (Document, required): The Role Profile.
		method (str, optional): The hook event name.

	Returns:
		None
	"""
	delete_role_profile_in_keycloak(doc)
