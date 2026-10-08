# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.

from frappe import _


def get_data():
	"""
	Describe the desk module icon (legacy desktop config).

	Returns:
	        list[dict]: One entry for the Keycloak Integration module.
	"""
	return [
		{"module_name": "Keycloak Integration", "type": "module", "label": _("Keycloak Integration")}
	]
