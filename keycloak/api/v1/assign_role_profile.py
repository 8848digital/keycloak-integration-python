import frappe
from frappe import _

@frappe.whitelist()
def assign_role_profile_in_frappe(kwargs):
    print(kwargs)
    try:
        erp_username = frappe.db.get_value("Erpnext Keycloak User Mapping", {"keycloak_id": kwargs["user_id"]}, "erpnext_username") 
        if frappe.db.exists("Erpnext User",erp_username):
            doc = frappe.get_doc("Erpnext User",erp_username)
            if kwargs.get("operation") == "assign":
                for row in kwargs.get("role_details"):
                    if frappe.db.exists("Role Profile", {"role_profile": row.get("name")}):
                        role_name = row.get("name")
                        if role_name:
                            doc.append("role_profiles", {
                                "role_profile": role_name
                            })
                    doc.save()
                    assign_collective_roles(erp_username)
            elif kwargs.get("operation") == "unassign":
                frappe.enqueue(remove_roles, kwargs=kwargs, erp_username=erp_username)         
        else:
            doc = frappe.new_doc("Erpnext User")
            doc.user = erp_username
            for row in kwargs.get("role_details"):
                if frappe.db.exists("Role Profile", {"role_profile": row.get("name")}):
                    role_name = row.get("name")
                    if role_name:
                        doc.append("role_profiles", {
                            "role_profile": role_name
                        })
                        doc.save()
                        assign_collective_roles(erp_username)
            
        doc.reload()     
    except Exception as e:
        print("ISSUE : ",e)
        frappe.log_error("Issue: " + str(e))


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

def remove_roles(kwargs, erp_username):
    try:
        # Extract roles to unassign
        roles_to_unassign = [row.get("name") for row in kwargs.get("role_details", [])]        
        if roles_to_unassign:
            if frappe.db.exists("Role Profile",{"role_profile": ("in", roles_to_unassign)}):
                frappe.db.delete(
                    "Role Profiles Table",
                    {
                        "parenttype": "Erpnext User",
                        "parent": erp_username,
                        "role_profile": ("in", roles_to_unassign)
                    }
                )

                # Reassign idx values correctly
                erp_user_doc = frappe.get_doc("Erpnext User",erp_username)
                for idx, row in enumerate(erp_user_doc.role_profiles, start=1):
                    row.idx = idx
                    
                erp_user_doc.save()

                assign_collective_roles(erp_username)
            else:
                print("No roles provided to unassign.")

    except Exception as e:
        print("ISSUE:", e)
        frappe.log_error(f"Issue in removing roles: {str(e)}")