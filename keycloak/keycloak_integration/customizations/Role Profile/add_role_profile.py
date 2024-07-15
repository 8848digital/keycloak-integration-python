import frappe
from frappe import _
import requests
# from frappe.utils import get_site_path()

def add_role_profile_in_keycloak(doc, method):
    if doc.is_new():
        token = get_access_token()
        create_new_role_profile(doc, token)

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

def create_new_role_profile(doc,access_token):
    try:
        url,headers = get_url_and_headers(access_token)
        role_profile_name = {
            "name": doc.role_profile
        }

        site_url = frappe.utils.get_url()
        if site_url:
            role_profile_name["attributes"] = {"site_url":[f"{site_url}"]}
        response = requests.post(url, headers=headers, json=role_profile_name)
        
        if response.status_code == 201:
            frappe.msgprint(_("Role Profile added successfully."))
        else:
            frappe.throw(_(response.text))
    except Exception as e:
        frappe.throw(_(f"Failed to add Role Profile. Error: {e}"))

def get_url_and_headers(access_token):
    doc = frappe.get_doc("Keycloak Details")
    url = f"{doc.url}/admin/realms/myrealm/roles"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    return url,headers


def delete_role_profile_in_keycloak(doc,method):
    try:
        access_token = get_access_token()
        url,headers = get_url_and_headers(access_token)
        mapped_doc = frappe.get_doc("Erpnext Keycloak Role Profile Mapping",doc.role_profile)

        delete_url = f"{url}/{mapped_doc.keycloak_realm_role_name}"
        response = requests.delete(delete_url, headers=headers)
        if response.status_code == 204:
            frappe.msgprint(_("Role deleted successfully."))
        else:
            frappe.throw(_(response.text))  
    except Exception as e:
        frappe.throw(_(f"Failed to delete role. Error: {e}")) 