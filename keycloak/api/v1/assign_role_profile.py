import frappe
from frappe import _
import json

@frappe.whitelist()
def assign_role_profile_in_frappe(kwargs):
    try:
        erp_username = frappe.db.get_value("Erpnext Keycloak User Mapping", {"keycloak_id": kwargs["user_id"]}, "erpnext_username")
        kwargs["role_details"] = json.loads(kwargs.get("role_details").replace("{", '{"').replace("=", '":"').replace(", ", '","').replace("}", '"}'))
        if frappe.db.exists("User Role Profiles",erp_username):
            if kwargs.get("operation") == "assign":
                doc = frappe.get_doc("User Role Profiles",erp_username)
                for row in kwargs.get("role_details"):
                    if row.get("id"):
                        role_name = frappe.get_value("Erpnext Keycloak Role Profile Mapping", {"role_profile_id":row.get("id")}, "role_profile_name")
                        if role_name:
                            doc.append("role_profiles", {
                                "role_profile": role_name
                            })
                doc.save()
                assign_collective_roles(erp_username)
            elif kwargs.get("operation") == "unassign":
                frappe.enqueue(remove_roles, kwargs=kwargs, erp_username=erp_username)
        else:
            doc = frappe.new_doc("User Role Profiles")
            doc.user = erp_username
            print("in else")
            for row in kwargs.get("role_details"):
                if row.get("id"):
                    role_name = frappe.get_value("Erpnext Keycloak Role Profile Mapping", {"role_profile_id":row.get("id")}, "role_profile_name")
                    if role_name:
                        doc.append("role_profiles", {
                            "role_profile": role_name
                        })
            doc.save()
            assign_collective_roles(erp_username)
        # doc.reload()
    except Exception as e:
        frappe.log_error("Issue: " + str(e))

def assign_collective_roles(erp_username):
    try:
        custom_user_doc = frappe.get_doc("User Role Profiles", erp_username)
        collected_roles = set()
        for row in custom_user_doc.role_profiles:
            role_profile_name = row.role_profile
            role_profile_doc = frappe.get_doc("Role Profile", role_profile_name)
            for role_row in role_profile_doc.roles:
                collected_roles.add(role_row.role)
        user_doc = frappe.get_doc("User", erp_username)
        user_doc.set("roles", [])
        user_doc.set("role_profile_name", None)
        for role in collected_roles:
            user_doc.append("roles", {"role": role})
        user_doc.save()
    except Exception as e:
        frappe.log_error("Issue: " + str(e))

def remove_roles(kwargs, erp_username):
    try:
        # Extract roles to unassign
        roles_to_unassign = None
        for row in kwargs.get("role_details"):
            roles_to_unassign = row.get("name")
        erp_role = frappe.db.get_value("Erpnext Keycloak Role Profile Mapping",{"keycloak_realm_role_name":roles_to_unassign}, "name")
        if roles_to_unassign:
            if frappe.db.exists("Role Profile",{"role_profile": erp_role}):
                frappe.db.delete(
                    "Role Profiles Table",
                    {
                        "parenttype": "User Role Profiles",
                        "parent": erp_username,
                        "role_profile": erp_role
                    }
                )

                # Reassign idx values correctly
                user_role_profiles = frappe.get_doc("User Role Profiles",erp_username)
                for idx, row in enumerate(user_role_profiles.role_profiles, start=1):
                    row.idx = idx
                    
                user_role_profiles.save()

                assign_collective_roles(erp_username)
            else:
                frappe.log_error("No roles provided to unassign.")
    except Exception as e:
        frappe.log_error(f"Issue in removing roles: {str(e)}")