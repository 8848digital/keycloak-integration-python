# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.

"""Derive the Keycloak URL fields of the "keycloak" Social Login Key."""

from keycloak.utils.keycloak_admin import KEYCLOAK_PROVIDER, join_url


def set_missing_url(doc):
	"""
	Keycloak needs both forms of its address: base_url
	("<root>/realms/<realm>") for OAuth and root_url + realm_name for the
	Admin API. Fill in whichever is missing from the other.

	Parameters:
	        doc (Document, required): The Social Login Key.

	Returns:
	        None
	"""
	if doc.name != KEYCLOAK_PROVIDER:
		return

	if not doc.base_url and doc.root_url and doc.realm_name:
		doc.base_url = join_url(doc.root_url, "realms", doc.realm_name)

	if doc.base_url and not doc.root_url and not doc.realm_name and "/realms/" in doc.base_url:
		root_url, realm_path = doc.base_url.split("/realms/", 1)
		doc.root_url = root_url + "/"
		doc.realm_name = realm_path.strip("/").split("/")[0]
