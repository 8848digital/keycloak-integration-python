import frappe
from frappe import _

@frappe.whitelist()
def assign_role_profile_in_frappe(kwargs):
    try:
        erp_username = frappe.db.get_value("Erpnext Keycloak User Mapping", {"keycloak_id": kwargs["user_id"]}, "erpnext_username")
        if erp_username is not None:
            doc = frappe.get_doc("User", erp_username)
            if kwargs["operation"] == "assign":
                doc.role_profile_name = kwargs["role_details"][0]["name"]
            elif kwargs["operation"] == "unassign":
                doc.role_profile_name = None
                if len(doc.roles) > 0:
                    doc.roles.clear()
            doc.save(ignore_permissions=True)
        else:
            frappe.log_error("Username not found")
    except Exception as e:
        frappe.log_error("Issue: " + str(e))