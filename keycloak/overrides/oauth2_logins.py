import frappe
from frappe.integrations.oauth2_logins import custom
import json


@frappe.whitelist(allow_guest=True)
def custom_keycloak_sso(code: str, state: str):
	path = frappe.request.path[1:].split("/")
	if len(path) == 4 and path[3]:
		provider = path[3]
		frappe.local.cookie_manager.set_cookie("provider", provider)
		url = frappe.safe_decode(frappe.request.query_string)
		frappe.log_error("SSO", url)
		frappe.local.cookie_manager.set_cookie(provider, json.dumps(url))
	custom(code = code, state = state)
		