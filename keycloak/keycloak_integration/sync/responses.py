# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.

"""Response shapes of the Keycloak sync endpoint (kept for existing clients)."""


def success_response(data=None):
	"""
	Build the legacy success payload.

	Parameters:
	        data (Any, optional): The payload.

	Returns:
	        dict: {"msg": "success", "data": data}
	"""
	return {"msg": "success", "data": data}


def error_response(err_msg):
	"""
	Build the legacy error payload.

	Parameters:
	        err_msg (str, required): The error message.

	Returns:
	        dict: {"msg": "error", "error": err_msg}
	"""
	return {"msg": "error", "error": str(err_msg)}
