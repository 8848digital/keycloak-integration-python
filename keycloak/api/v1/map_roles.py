import frappe
from frappe import _

@frappe.whitelist()
def map_roles_in_frappe(kwargs):
	if kwargs["operation"] == "create":
		create_role_profile_map(kwargs)
	elif kwargs["operation"] == "delete":
		delete_role_profile_map(kwargs)
		
def create_role_profile_map(kwargs):
	try:
		doc = frappe.new_doc("Erpnext Keycloak Role Profile Mapping")
		doc.role_profile_name = kwargs["role_profile_details"]["name"]
		doc.role_profile_id = kwargs["role_profile_details"]["id"]
		doc.role_profile_site_name = kwargs.get("updated_keycloak_name")
		doc.save(ignore_permissions=True)
	except Exception as e:
		frappe.log_error("Unable to create role profile map", e)

def delete_role_profile_map(kwargs):
	try:
		if frappe.db.exists("Erpnext Keycloak Role Profile Mapping", kwargs["role_profile_name"]):
			frappe.delete_doc("Erpnext Keycloak Role Profile Mapping", kwargs["role_profile_name"])
		else:
			frappe.log_error("Role Profile Map not found in frappe")
	except Exception as e:
		frappe.log_error("Unable to delete Role Profile Map : ", e)