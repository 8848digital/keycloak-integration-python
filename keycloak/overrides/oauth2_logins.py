import frappe
from keycloak.utils.oauth import login_via_oauth2
from frappe.integrations.oauth2_logins import decoder_compat


@frappe.whitelist(allow_guest=True)
def custom(code: str, state: str):
	"""
	Callback for processing code and state for user added providers

	process social login from /api/method/frappe.integrations.custom/<provider>
	"""
	path = frappe.request.path[1:].split("/")
	if len(path) == 4 and path[3]:
		provider = path[3]
		# Validates if provider doctype exists
		if frappe.db.exists("Social Login Key", provider):
			login_via_oauth2(provider, code, state, decoder=decoder_compat)