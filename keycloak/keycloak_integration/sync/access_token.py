# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.

"""Exchange a username and password for the user's API token."""

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils.password import check_password

from keycloak.keycloak_integration.sync.responses import error_response, success_response


# Guests can call this, so slow down password guessing per IP.
@rate_limit(limit=10, seconds=60 * 10)
def get_access_token(payload):
	"""
	Verify the user's password and return the user's existing API key and
	secret as a "token <key>:<secret>" header value. Failed attempts all get
	the same message, so the endpoint does not reveal which users exist.

	Parameters:
	        payload (dict, required): Needs "usr" and "pwd".

	Returns:
	        dict: success_response with {"access_token"} or error_response.
	"""
	usr, pwd = payload.get("usr"), payload.get("pwd")
	if not usr or not pwd:
		return error_response(_("Username and password are required"))

	try:
		usr = check_password(usr, pwd)
	except frappe.AuthenticationError:
		return error_response(_("Incorrect username or password"))

	user = frappe.get_doc("User", usr)
	if not user.enabled:
		return error_response(_("Incorrect username or password"))

	api_secret = user.get_password("api_secret", raise_exception=False) if user.api_key else None
	if not api_secret:
		return success_response(data={})

	return success_response(data={"access_token": f"token {user.api_key}:{api_secret}"})
