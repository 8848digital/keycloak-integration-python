import frappe
from frappe import _
import requests

def add_module_profile_in_keycloak(doc, method):
    token = get_access_token()
    if doc.is_new():
        create_new_module_profile(doc, token)

def get_access_token():
    try:
        doc = frappe.get_doc("Keycloak Details")
        url = f'{doc.url}/realms/myrealm/protocol/openid-connect/token'
        payload = {
            'client_id': doc.client_id,
            'client_secret': doc.client_secret,
            'grant_type': 'client_credentials'
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        response = requests.post(url, headers=headers, data=payload)
        data = response.json()
        return data["access_token"]
    
    except Exception as e:
        frappe.throw(_("An error occured while generating token : ",e))

def create_new_module_profile(doc,access_token):
    try:
        url,headers = get_url_and_headers(access_token)
        if frappe.db.exists("Keycloak Erpnext Group Mapping","Module Profile"):
            group_id = frappe.db.get_value("Keycloak Erpnext Group Mapping","Module Profile","group_id")
        else:
            frappe.msgprint("Group Module Profile not found")
        url_endpoint = f"{url}/{group_id}/children"
        payload = {
            "name": doc.module_profile_name
        }
        response = requests.post(url_endpoint, headers=headers, json=payload)
        if response.status_code == 201:
            frappe.msgprint(_("Module Profile added successfully."))
        else:
            frappe.throw(_(response.text))
    except Exception as e:
        frappe.throw(_(f"Failed to add Module Profile. Error: {e}"))

def get_url_and_headers(access_token):
    doc = frappe.get_doc("Keycloak Details")
    url = f"{doc.url}/admin/realms/myrealm/groups"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    return url,headers

def delete_module_profile_in_keycloak(doc,method):
    try:
        module_profile_id = None
        access_token = get_access_token()
        url,headers = get_url_and_headers(access_token)
        d = frappe.get_doc("Keycloak Erpnext Group Mapping","Module Profile")
        for row in d.module_profile_details:
            if row.module_name == doc.name:
                module_profile_id = row.module_id
                break
        if module_profile_id is not None:
            delete_url = f"{url}/{module_profile_id}"
            response = requests.delete(delete_url,headers=headers)
            if response.status_code == 204:
                frappe.msgprint(_("Role deleted successfully."))
            else:
                frappe.throw(_(response.text))  
    except Exception as e:
        frappe.throw(_(f"Failed to delete module profile. Error: {e}")) 