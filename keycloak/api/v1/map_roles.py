import frappe
from frappe import _
from keycloak.utils import error_response
import json


@frappe.whitelist()
def map_roles_in_frappe(kwargs):
	try:
		erp_username = frappe.db.get_value("Erpnext Keycloak User Mapping",{"keycloak_id": kwargs["user_id"]},"erpnext_username")
		if erp_username is not None:
			doc = frappe.get_doc("User",erp_username)
			doc.role_profile_name = kwargs["role_details"][0]["name"] if kwargs["operation"] == "assign" else None
			doc.save(ignore_permissions=True)
		else:
			print("Username not found")
	except Exception as e:
		print(e)