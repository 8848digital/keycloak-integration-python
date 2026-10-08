# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.

"""
Configuration for docs
"""

# source_link = "https://github.com/[org_name]/keycloak"
# headline = "App that does everything"
# sub_heading = "Yes, you got that right the first time, everything"


def get_context(context):
	"""
	Set the brand shown on the generated docs pages.

	Parameters:
	        context (frappe._dict, required): The page context.

	Returns:
	        None
	"""
	context.brand_html = "Keycloak Integration"
