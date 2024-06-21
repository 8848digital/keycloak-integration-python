__version__ = "0.0.1"


import keycloak.overrides.oauth
import frappe.utils.oauth

frappe.utils.oauth.get_info_via_oauth = keycloak.overrides.oauth.get_info_via_oauth
