# import frappe
# from frappe import _
# from frappe.utils import escape_html
# from frappe.website.utils import is_signup_disabled
# import requests

# @frappe.whitelist(allow_guest=True)
# def sign_up(email, full_name, redirect_to):
#     print("INSIDE SIGN UP FUNCTION HOOKS")
#     if is_signup_disabled():
#         frappe.throw(_("Sign Up is disabled"), title=_("Not Allowed"))

#     user = frappe.db.get("User", {"email": email})
#     if user:
#         if user.enabled:
#             return 0, _("Already Registered")
#         else:
#             return 0, _("Registered but disabled")
#     else:
#         if frappe.db.get_creation_count("User", 60) > 300:
#             frappe.respond_as_web_page(
#                 _("Temporarily Disabled"),
#                 _(
#                     "Too many users signed up recently, so the registration is disabled. Please try back in an hour"
#                 ),
#                 http_status_code=429,
#             )

#         from frappe.utils import random_string

#         user = frappe.get_doc(
#             {
#                 "doctype": "User",
#                 "email": email,
#                 "first_name": escape_html(full_name),
#                 "enabled": 1,
#                 "new_password": random_string(10),
#                 "user_type": "Website User",
#             }
#         )
#         user.flags.ignore_permissions = True
#         user.flags.ignore_password_policy = True
#         user.insert()
#         create_user_in_keycloak(user)

#         # set default signup role as per Portal Settings
#         default_role = frappe.db.get_single_value("Portal Settings", "default_role")
#         if default_role:
#             user.add_roles(default_role)

#         if redirect_to:
#             frappe.cache().hset("redirect_after_login", user.name, redirect_to)
        
#         if user.flags.email_sent:
#             return 1, _("Please check your email for verification")
#         else:
#             return 2, _("Please ask your administrator to verify your sign-up")

# def create_user_in_keycloak(user):
#     print(user.as_dict())
#     token = get_access_token()
#     create_new_user(user, token)



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
#         data = response.json()
#         return data["access_token"]
    
#     except Exception as e:
#         frappe.throw(_("An error occured while generating token : ",e))

# def create_new_user(doc, access_token):
#     try:
#         print("IN TRY BLOCK")
#         parameters_map = map_fieldnames_of_erp_and_keycloak()
#         url,headers = get_url_and_headers(access_token)

#         user_data_for_creation = {}
#         for key, value in doc.as_dict().items():
#             if key in parameters_map:
#                 user_data_for_creation[parameters_map[key]] = value

#         user_data_for_creation["enabled"] = True
        
#         response = requests.post(url, headers=headers, json=user_data_for_creation)
#         print(response.status_code)
#         frappe.msgprint(_("User added successfully in Keycloak."))
      
#     except Exception as e:
#         print("IN ELSE BLOCK")
#         print(type(e))
#         # frappe.throw(_(f"Failed to add the user. Error: {e}"))


# def map_fieldnames_of_erp_and_keycloak():
#     parameters_map = {
#         "first_name": "firstName",
#         "last_name": "lastName",
#         "username": "username",
#         "email": "email"
#     }
#     return parameters_map


# def get_url_and_headers(access_token):
#     url = "http://localhost:8080/admin/realms/myrealm/users"
#     headers = {
#         "Content-Type": "application/json",
#         "Authorization": f"Bearer {access_token}"
#     }
#     return url,headers