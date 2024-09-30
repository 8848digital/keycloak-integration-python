import frappe
from frappe import _
import json
import requests
from keycloak.utils.utils import get_keycloak_access_token

@frappe.whitelist()
def assign_role_profile_in_frappe(kwargs):
    erp_username = frappe.db.get_value("Erpnext Keycloak User Mapping", {"keycloak_id": kwargs["user_id"]}, "erpnext_username")
    kwargs["role_details"] = json.loads(kwargs.get("role_details").replace("{", '{"').replace("=", '":"').replace(", ", '","').replace("}", '"}'))
    if kwargs.get("operation") == "assign":
        if frappe.db.exists("User Role Profiles",erp_username):
            doc = frappe.get_doc("User Role Profiles",erp_username)
        else:
            doc = frappe.new_doc("User Role Profiles")
            doc.user = erp_username
        for row in kwargs.get("role_details"):
            if row.get("id"):
                role_profile = frappe.get_value("Erpnext Keycloak Role Profile Mapping", {"role_profile_id":row.get("id")}, "role_profile_name")
                if role_profile:
                    doc.append("role_profiles", {
                        "role_profile": role_profile
                    })
        doc.save()
        assign_collective_roles(erp_username)
    elif kwargs.get("operation") == "unassign":
        frappe.enqueue(remove_roles, kwargs=kwargs, erp_username=erp_username)

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
    try:
        # Extract roles to unassign
        roles_to_unassign = None
        for row in kwargs.get("role_details"):
            roles_to_unassign = row.get("name")
        role_profile = frappe.db.get_value("Erpnext Keycloak Role Profile Mapping",{"keycloak_realm_role_name":roles_to_unassign}, "name")
        if roles_to_unassign:
            if frappe.db.exists("Role Profile",{"role_profile": role_profile}):
                frappe.db.delete(
                    "Role Profiles Table",
                    {
                        "parenttype": "User Role Profiles",
                        "parent": erp_username,
                        "role_profile": role_profile
                    }
                )

                # Reassign idx values correctly
                rpt = frappe.get_all("Role Profiles Table", filters = {"parenttype": "User Role Profiles", "parent": erp_username}, pluck = "name", order_by = "idx")
                idx = 1
                for row in rpt:
                    frappe.db.set_value("Role Profiles Table", row, "idx", idx)
                    idx += 1
                roles_to_remove = get_collective_roles(erp_username, role_profile, "remove")
                if len(rpt) > 0:
                    remove_user_roles(erp_username, roles_to_remove)
                else:
                    remove_user_roles(erp_username, roles_to_remove)
                    frappe.delete_doc("User Role Profiles",erp_username)
            else:
                frappe.log_error("No roles provided to unassign.")
    except Exception as e:
        assign_role_profile_in_keycloak(kwargs)
        raise

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

def assign_role_profile_in_keycloak(kwargs):
    base_url = frappe.get_value("Social Login Key", "keycloak", "base_url").strip("/")
    realm = base_url.split('/')[-1]
    base_url = base_url.replace("realms", "admin/realms")
    url = "{}/{}/users/{}/role-mappings/realm".format(base_url, realm, kwargs["user_id"])
    payload = [{'id': kwargs["role_details"][0]["id"], 'name': kwargs["role_details"][0]["name"]}]
    access_token = get_keycloak_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 204:
        frappe.log_error({"response": response.text, "keycloak_user_id": kwargs["user_id"], "keycloak_role": kwargs["role_details"][0]["name"]}, f"Unable To Assign Role: {kwargs["role_details"][0]["name"]} In Keycloak")
