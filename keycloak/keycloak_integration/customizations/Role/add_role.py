import frappe
from frappe import _
import requests

def add_role_in_keycloak(doc, method):
    print("1")
    token = get_access_token()
    print(token)
    if doc.is_new():
        create_new_realm_role(doc, token)
    # else:
    #     update_existing_role(doc, token)

def get_access_token():
    try:
        url = 'http://localhost:8080/realms/myrealm/protocol/openid-connect/token'
        payload = {
            'client_id': 'admin-rest-client1',
            'client_secret': '8SA2BtQ60bJujyS9FM24Q2fqiQwjLiKs',
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

def create_new_realm_role(doc,access_token):
    try:
        parameters_map = map_fieldnames_of_erp_and_keycloak()
        url,headers = get_url_and_headers(access_token)

        user_data_for_creation = {}
        print(doc.as_dict())
        for key, value in doc.as_dict().items():
            pass
            if key in parameters_map:
                user_data_for_creation[parameters_map[key]] = value

        response = requests.post(url, headers=headers, json=user_data_for_creation)

        if response.status_code == 201:
            frappe.msgprint(_("Role added successfully."))
        else:
            frappe.throw(_(response.text))
    except Exception as e:
        frappe.throw(_(f"Failed to add role. Error: {e}"))


# def update_existing_role(doc, access_token):
#     try:
#         print("INSIDE FUNCTION")
#         print(doc.as_dict(),"DOC.AS_DICT")
#         parameters_map = map_fieldnames_of_erp_and_keycloak()
#         url,headers = get_url_and_headers(access_token)

#         response = requests.get(url, headers=headers)
#         roles_data = response.json()
#         print("RESPONSE DATA : ",roles_data)


#         doc_keys = doc.as_dict()
#         for role in roles_data:
#             if role["name"] == doc.name:
#                 role_data_to_update = {}
#                 for key, value in doc_keys.items():
#                     if key in parameters_map:
#                         role_data_to_update[parameters_map[key]] = value

#                 update_url = f"{url}/{role['name']}"
#                 print("UPDATE URL : ",update_url)
#                 print("ROLE DATA : ",role_data_to_update)
#                 update_response = requests.put(update_url, headers=headers, json=role_data_to_update)
#                 if update_response.status_code == 204:
#                     frappe.msgprint(_("Role updated successfully."))
#                 else:
#                     frappe.throw(_(update_response.text))
#     except Exception as e:
#         frappe.throw(_(f"Failed to update role. Error: {e}"))



def map_fieldnames_of_erp_and_keycloak():
    parameters_map = {
        "name": "name",
    }
    return parameters_map

def get_url_and_headers(access_token):
    url = "http://localhost:8080/admin/realms/myrealm/roles"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    return url,headers

def delete_role_in_keycloak(doc,method):
    try:
        access_token = get_access_token()
        url,headers = get_url_and_headers(access_token)

        response = requests.get(url, headers=headers)
        roles_list = response.json()

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