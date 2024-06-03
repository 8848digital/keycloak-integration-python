# import frappe
# import requests
# import json
# from frappe import _

# def after_insert_check(doc,method):
#     print("1")
#     print(doc.username)

# def before_insert_check(doc,method):
#     print("2") 
#     print(doc.username)

# def validate_check(doc,method):
#     print("3")
#     print(doc.username)

# def add_user_in_keycloak(doc, method):
#     if frappe.session.user != "keycloak-client@gmail.com":
#         token = get_access_token()
#         create_new_user_entry(doc,token)
#     # if doc.is_new():
#     #     create_new_user_entry(doc, token)
#     # else:
#     #     update_existing_data(doc, token)

# def get_access_token():
#     try:
#         doc = frappe.get_doc("Keycloak Details")
#         url = f'{doc.url}/realms/myrealm/protocol/openid-connect/token'
#         payload = {
#             'client_id': doc.client_id,
#             'client_secret': doc.client_secret,
#             'grant_type': 'client_credentials'
#         }
#         headers = {
#             'Content-Type': 'application/x-www-form-urlencoded'
#         }

#         response = requests.post(url, headers=headers, data=payload)
#         data = response.json()
#         print(data)
#         return data["access_token"]
    
#     except Exception as e:
#         frappe.throw(_("An error occured while generating token : ",e))


# def create_new_user_entry(doc, access_token):
#     try:
#         parameters_map = map_fieldnames_of_erp_and_keycloak()
#         url,headers = get_url_and_headers(access_token)

#         user_data_for_creation = {}
#         for key, value in doc.as_dict().items():
#             if key in parameters_map:
#                 user_data_for_creation[parameters_map[key]] = value

#         user_data_for_creation["enabled"] = True
        
#         response = requests.post(url, headers=headers, json=user_data_for_creation)
        
#         if response.status_code == 201:
#             frappe.msgprint(_("User added successfully."))
#         else:
#             frappe.throw(_(response.text))
#     except Exception as e:
#         frappe.throw(_(f"Failed to add user. Error: {e}"))

# def update_existing_data(doc, access_token):
#     try:
#         parameters_map = map_fieldnames_of_erp_and_keycloak()
#         url,headers = get_url_and_headers(access_token)
#         print("3")
#         response = requests.get(url, headers=headers)
#         users_data = response.json()

#         doc_keys = doc.as_dict()
#         for user in users_data:
#             if user["email"] == doc.email:
#                 user_fields_to_update = {}
#                 for key, value in doc_keys.items():
#                     if key in parameters_map:
#                         user_fields_to_update[parameters_map[key]] = value

#                 update_url = f"{url}/{user['id']}"
#                 update_response = requests.put(update_url, headers=headers, json=user_fields_to_update)
#                 if update_response.status_code == 204:
#                     frappe.msgprint(_("User data updated successfully."))
#                 else:
#                     frappe.throw(_(update_response.text))
#     except Exception as e:
#         frappe.throw(_(f"Failed to update user data. Error: {e}"))


# def map_fieldnames_of_erp_and_keycloak():
#     parameters_map = {
#         "first_name": "firstName",
#         "last_name": "lastName",
#         "username": "username",
#         "email": "email"
#     }
#     return parameters_map


# def get_url_and_headers(access_token):
#     doc = frappe.get_doc("Keycloak Details")
#     url = f"{doc.url}/admin/realms/myrealm/users"
#     headers = {
#         "Content-Type": "application/json",
#         "Authorization": f"Bearer {access_token}"
#     }
#     return url,headers


# def delete_user_in_keycloak(doc,method):
#     try:
#         access_token = get_access_token()
#         url,headers = get_url_and_headers(access_token)

#         response = requests.get(url, headers=headers)
#         users_list = response.json()

#         for entry in users_list:
#             if entry["email"] == doc.email:
#                 delete_url = f"{url}/{entry['id']}"
#                 response = requests.delete(delete_url, headers=headers)
#                 if response.status_code == 204:
#                     frappe.msgprint(_("User deleted successfully."))
#                     break
#                 else:
#                     frappe.throw(_(response.text))  
#         else:
#             frappe.throw(_("User does not exist in Keycloak"))
#     except Exception as e:
#         frappe.throw(_(f"Failed to delete user. Error: {e}"))