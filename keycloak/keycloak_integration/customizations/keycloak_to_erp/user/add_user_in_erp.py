# import frappe
# from frappe import _
# from frappe.utils.response import build_response
# import json


# print("AMan")


# @frappe.whitelist(allow_guest=True)
# def build_response(status, data=None, message=None):
#     response = {
#         "status": status
#     }
#     if data is not None:
#         response["data"] = data
#     if message is not None:
#         response["message"] = message
#     return response


# @frappe.whitelist(allow_guest=True)
# def getdata(kwargs):
#     try:
#         print("wbdcui")
#         print(kwargs)
#         # body = json.loads(frappe.request.data)
#         # print(body)
#         if kwargs["operation"] == "create":
#             create_new_user(kwargs)
#         elif kwargs["operation"] == "delete":
#             delete_new_user(kwargs)
#         # doc = frappe.db.get_list("custom task invoice")
#         # return build_response("success")
#     except Exception as e:
#         print(e)
   
# def create_new_user(kwargs):
#     try:
#         print(kwargs,"KWARGS IN NEW USER FUNCTION")
#         print("1")
#         doc = frappe.new_doc("User")
#         doc.email = kwargs["email"]
#         doc.first_name = kwargs["firstName"]
#         print("2")
#         doc.save(ignore_permissions=True)
#         print("3")
#         frappe.msgprint("USER ADDED")
#     except Exception as e:
#         print("ISSUE : ",e)


# def delete_new_user(kwargs):
#     try:
#         print("1")
#         # if frappe.db.exists("User")
#     except:
#         frappe.throw("User not present")