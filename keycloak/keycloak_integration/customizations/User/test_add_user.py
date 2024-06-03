# import frappe
# import requests
# from frappe import _

# def add_user_in_erpnext():
#     access_token = get_access_token()

#     parameters_map = map_fieldnames_of_erp_and_keycloak()
#     url,headers = get_url_and_headers(access_token)

#     response = requests.get(url, headers=headers)
#     users_list = response.json()
#     print(users_list,"USER")
#     for entry in users_list:
#         if not frappe.db.exists("User",entry["email"]):
#             doc = frappe.new_doc("User")
#             for key,value in entry.items():
#                 if key in parameters_map:
#                     doc.set(parameters_map[key], value)
#             doc.save()

# def get_access_token():
#     try:
#         url = 'http://localhost:8080/realms/myrealm/protocol/openid-connect/token'
#         payload = {
#             'client_id': 'admin-rest-client1',
#             'client_secret': '8SA2BtQ60bJujyS9FM24Q2fqiQwjLiKs',
#             'grant_type': 'client_credentials'
#         }
#         headers = {
#             'Content-Type': 'application/x-www-form-urlencoded'
#         }

#         response = requests.post(url, headers=headers, data=payload)
#         data_credentials = response.json()
#         return data_credentials["access_token"]
    
#     except Exception as e:
#         frappe.throw(_("An error occured while generating token : ",e))


# def get_url_and_headers(access_token):
#     url = "http://localhost:8080/admin/realms/myrealm/users"
#     headers = {
#         "Content-Type": "application/json",
#         "Authorization": f"Bearer {access_token}"
#     }
#     return url,headers

# def map_fieldnames_of_erp_and_keycloak():
#     parameters_map = {
#         "firstName":"first_name",
#         "lastName":"last_name",
#         "username": "username",
#         "email": "email"
#     }
#     return parameters_map
