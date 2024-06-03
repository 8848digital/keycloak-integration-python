import frappe
from frappe import _
import json

print("AMan")

@frappe.whitelist()
def map_users_in_frappe(kwargs):
	if kwargs["operation"] == "create":
		create_user_in_frappe(kwargs)
	elif kwargs["operation"] == "delete":
		delete_user_in_frappe(kwargs)

def create_user_in_frappe(kwargs):
	print(kwargs)
	user = frappe.new_doc("User")
	user.email = kwargs.get("email")
	user.username = kwargs.get("userName")
	user.first_name = kwargs.get("firstName")
	user.last_name = kwargs.get("lastName")
	user.save(ignore_permissions=True)
	kwargs["erpnext_username"] = user.name
	create_frappe_keycloak_user_map(kwargs)

def create_frappe_keycloak_user_map(kwargs):
	print(kwargs)
	try:
		doc = frappe.new_doc("Erpnext Keycloak User Mapping")
		doc.erpnext_username = kwargs.get("erpnext_username")
		doc.keycloak_id = kwargs.get("id")
		doc.save(ignore_permissions=True)
	except Exception as e:	
		print(e)

def delete_user_in_frappe(kwargs):
	try:
		erp_username = frappe.db.get_value("Erpnext Keycloak User Mapping",{"keycloak_id": kwargs["id"]},"erpnext_username")
		print(erp_username,"ERP USERNAME")
		if erp_username is not None:
				frappe.delete_doc("User",erp_username)
				frappe.delete_doc("Erpnext Keycloak User Mapping",erp_username)
				print("Doc deleted")
		else:
			print("Username not found in frappe")
	except Exception as e:
		print("Issue : ",e)