import frappe
from frappe import _
import json

@frappe.whitelist()
def assign_role_profile_in_frappe(kwargs):
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
            remove_roles(kwargs=kwargs, erp_username=erp_username)
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

def assign_collective_roles(erp_username):
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

def remove_roles(kwargs, erp_username):
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
            rpt = frappe.get_all("Role Profiles Table", filters = {"parenttype": "User Role Profiles", "parent": erp_username}, pluck = "name", order_by = "idx")
            idx = 1
            for row in rpt:
                frappe.db.set_value("Role Profiles Table", row, "idx", idx)
                idx += 1
            roles_to_remove = get_collective_roles(erp_username, erp_role, "remove")
            if len(rpt) > 0:
                remove_user_roles(erp_username, roles_to_remove)
            else:
                remove_user_roles(erp_username, roles_to_remove)
                frappe.delete_doc("User Role Profiles",erp_username)
        else:
            frappe.log_error("No roles provided to unassign.")

def remove_user_roles(erp_username, roles_to_remove):
    for role in roles_to_remove:
        frappe.db.delete(
                        "Has Role",
                        {
                            "parenttype": "User",
                            "parent": erp_username,
                            "role": role
                        }
                    )

def get_collective_roles(erp_username, role_profile, operation_type = None):
    query = f"""SELECT DISTINCT hr.role 
                FROM `tabRole Profile` as rp
                JOIN `tabHas Role` as hr on hr.parent = rp.role_profile 
                WHERE hr.parenttype = "Role Profile"
                and rp.role_profile = %s
                and hr.role {"Not In" if operation_type == "remove" else "In"} (
                    SELECT hr.role 
                    FROM `tabUser Role Profiles` as urp 
                    JOIN `tabRole Profiles Table` as rpt on urp.name = rpt.parent 
                    JOIN `tabHas Role` as hr on hr.parent = rpt.role_profile 
                    WHERE hr.parenttype = "Role Profile" 
                    and urp.user = %s
                    )
                and hr.role {"In" if operation_type == "remove" else "Not In"} (SELECT DISTINCT hr.role 
                                FROM `tabHas Role` as hr
                                WHERE hr.parenttype = "User"
                                AND hr.parent = %s)
                """
    roles = frappe.db.sql(query, (role_profile, erp_username, erp_username), as_dict=1)
    role_list = []
    for role in roles:
        role_list.append(role.get("role"))
    return role_list