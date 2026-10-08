# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.

"""Keycloak SSO callback: Frappe's standard flow plus two small additions."""

import frappe
from frappe import _
from frappe.integrations.oauth2_logins import decoder_compat
from frappe.utils.oauth import get_info_via_oauth, login_oauth_user

from keycloak.keycloak_integration.sso_session import delete_keycloak_session, remember_sso_session
from keycloak.utils.keycloak_admin import KEYCLOAK_PROVIDER


# Reviewed: the identity provider redirects a not-yet-logged-in browser here.
@frappe.whitelist(allow_guest=True)  # nosemgrep
def login_via_keycloak(code: str, state: str, session_state: str | None = None, **kwargs):
	"""
	Complete a Keycloak login exactly like Frappe's standard
	`login_via_keycloak` (fetch userinfo, then log in / sign up the user).
	It also keeps the userinfo for the on_login role sync, and remembers
	Keycloak's session id, so logging out of ERPNext ends the Keycloak session.

	**Endpoint:** `/api/method/frappe.integrations.oauth2_logins.login_via_keycloak`
	(overrides the standard method via `override_whitelisted_methods`)
	**HTTP Method:** GET (redirect from Keycloak)
	**Parameters:**
	        - code (str, required): The OAuth authorization code.
	        - state (str, required): The OAuth state issued by Frappe.
	        - session_state (str, optional): Keycloak's SSO session id.
	        - Other keys (optional): Ignored (for example "iss").
	**Response:**
	A redirect to the desk (or the "redirect_to" stored in state), set by
	Frappe's login flow. On failure, Frappe's standard error page; a user
	without a User Permission gets an "access not set up" page (HTTP 403).
	"""
	userinfo = get_info_via_oauth(KEYCLOAK_PROVIDER, code, decoder_compat)
	frappe.flags.keycloak_userinfo = userinfo
	try:
		login_oauth_user(userinfo, provider=KEYCLOAK_PROVIDER, state=state)
	except frappe.AuthenticationError:
		__refuse_without_access(session_state)
		return

	if session_state:
		remember_sso_session(KEYCLOAK_PROVIDER, session_state)


def __refuse_without_access(session_state):
	"""
	The User Permission rule refused the login. Keep the user that Frappe
	just created on first login (and the synced roles), so an administrator
	can grant access; end the Keycloak session that has no ERPNext session;
	and show a clear page instead of a bare 401.

	Parameters:
	        session_state (str, optional): Keycloak's session id.

	Returns:
	        None
	"""
	# GET requests are rolled back; Frappe's own login_oauth_user commits for the same reason.
	frappe.db.commit()  # nosemgrep
	if session_state:
		delete_keycloak_session(session_state, notify=False)

	frappe.respond_as_web_page(
		_("Access not set up"),
		_(
			"You signed in with Keycloak, but your ERPNext access is not set up yet. Ask your administrator to give you a User Permission, then sign in again."
		),
		http_status_code=403,
		indicator_color="orange",
	)
