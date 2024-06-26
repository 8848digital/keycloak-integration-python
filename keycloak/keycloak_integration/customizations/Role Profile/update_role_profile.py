import frappe
from frappe import _

def update_user_roles(doc, method): 
    if not doc.is_new():
        print("I")
        lists = frappe.db.get_all("Role Profiles Table",filters={"role_profile":doc.role_profile},fields=["parent"])
        frappe.enqueue(assign_roles_based_on_selected_role_profiles,lists=lists)
    


def assign_roles_based_on_selected_role_profiles(lists):
    for role_profiles in lists:
        assign_collective_roles(role_profiles.parent)

def assign_collective_roles(erp_username):
    try:
        custom_user_doc = frappe.get_doc("Erpnext User", erp_username)
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