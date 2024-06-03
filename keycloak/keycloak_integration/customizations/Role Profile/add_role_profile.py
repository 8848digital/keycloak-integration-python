import frappe
from frappe import _
import requests

def add_role_profile_in_keycloak(doc, method):
    print("1")
    token = get_access_token()
    print(token)
    if doc.is_new():
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

# def create_new_role_profile(doc,access_token):
#     try:
#         parameters_map = map_fieldnames_of_erp_and_keycloak()
#         url,headers = get_url_and_headers(access_token)
#         print("FINE TILL HERE")
#         user_data_for_creation = {}
#         print(doc.as_dict())
#         for key, value in doc.as_dict().items():
#             if key in parameters_map:
#                 user_data_for_creation[parameters_map[key]] = value

#         print("ZZZZZZZZZZZZZZZZZZ")

#         response = requests.post(url, headers=headers, json=user_data_for_creation)
#         print("ALL OK")
#         print(response.status_code)
#         if response.status_code == 201:
#             frappe.msgprint(_("Role Profile added successfully."))
#         else:
#             frappe.throw(_(response.text))
#     except Exception as e:
#         frappe.throw(_(f"Failed to add Role Profile. Error: {e}"))

def create_new_role_profile(doc,access_token):
    try:
        parameters_map = map_fieldnames_of_erp_and_keycloak()
        url,headers = get_url_and_headers(access_token)
        user_data_for_creation = {}
        for key, value in doc.as_dict().items():
            if key in parameters_map:
                user_data_for_creation[parameters_map[key]] = value
            
        for role in doc.roles:
            if role.role in attributes:
                attributes[role.role] = ['1']

        print(attributes)
        user_data_for_creation["attributes"] = attributes

        response = requests.post(url, headers=headers, json=user_data_for_creation)
 
        if response.status_code == 201:
            frappe.msgprint(_("Role Profile added successfully."))
        else:
            frappe.throw(_(response.text))
    except Exception as e:
        frappe.throw(_(f"Failed to add Role Profile. Error: {e}"))

def map_fieldnames_of_erp_and_keycloak():
    parameters_map = {
        "role_profile": "name",
    }
    return parameters_map

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

        response = requests.get(url, headers=headers)
        roles_list = response.json()
        print(roles_list,"Roles list")
        for entry in roles_list:
            if entry["name"] == doc.name:
                delete_url = f"{url}/{entry['name']}"
                response = requests.delete(delete_url, headers=headers)
                if response.status_code == 204:
                    frappe.msgprint(_("Role deleted successfully."))
                    break
                else:
                    frappe.throw(_(response.text))  
        else:
            frappe.throw(_("Role does not exist in Keycloak"))
    except Exception as e:
        frappe.throw(_(f"Failed to delete role. Error: {e}")) 


attributes = {
    "Academics User": ["0"],
    "Account Manager": ["0"],
    "Accounts User": ["0"],
    "Agriculture Manager": ["0"],
    "Agriculture User": ["0"]
}