import frappe
from frappe import _
import requests

def add_module_profile_in_keycloak(doc, method):
    print("1")
    token = get_access_token()
    print(token)
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
        parameters_map = map_fieldnames_of_erp_and_keycloak()
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

def map_fieldnames_of_erp_and_keycloak():
    parameters_map = {
        "role_profile": "name",
    }
    return parameters_map

def get_url_and_headers(access_token):
    doc = frappe.get_doc("Keycloak Details")
    url = f"{doc.url}/admin/realms/myrealm/groups"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    return url,headers

def delete_module_profile_in_keycloak(doc,method):
    print("INSIDE DELETE")
    try:
        print("00")
        module_profile_id = None
        access_token = get_access_token()
        url,headers = get_url_and_headers(access_token)
        d = frappe.get_doc("Keycloak Erpnext Group Mapping","Module Profile")
        print(d.group_id)
        print("11")
        for row in d.module_profile_details:
            print("ROW MODULE NAME : ",row.module_name, " , DOC NAME : ",doc.name)
            if row.module_name == doc.name:
                
                module_profile_id = row.module_id
                print("1")
                break
        print(module_profile_id,"MODULE ID")
        print("22")
        if module_profile_id is not None:
            print("33")
            delete_url = f"{url}/{module_profile_id}"
            print(delete_url)
            response = requests.delete(delete_url,headers=headers)
            print(response.status_code)

    except Exception as e:
        frappe.throw(_(f"Failed to delete module profile. Error: {e}")) 


