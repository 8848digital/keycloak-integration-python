import frappe

@frappe.whitelist()
def map_user_type_in_frappe(kwargs):
	print(kwargs)
	try:
		erp_username = frappe.db.get_value("Erpnext Keycloak User Mapping",{"keycloak_id": kwargs["user_id"]},"erpnext_username")
		if erp_username is not None:
			doc = frappe.get_doc("User",erp_username)
			print(kwargs["group_details"]["name"])
			print(doc.user_type)
			doc.user_type = kwargs["group_details"]["name"]
			doc.save(ignore_permissions=True)
		else:
			print("Username not found")
	except Exception as e:
		print(e)
# 	if kwargs["operation"] == "assign":
# 		pass
# 		create_group_mapping(kwargs)
# 	elif kwargs["operation"] == "delete":
# 		pass
# 	print("PYTHON GROUPS")
# 	print(kwargs)
	
# def create_group_mapping(kwargs):
# 	try:
# 		doc = frappe.new_doc("Keycloak Erpnext Group Mapping")
# 		doc.group_id = kwargs["group_details"]["id"]
# 		doc.group_name = kwargs["group_details"]["name"]
# 		doc.save(ignore_permissions=True)
# 	except Exception as e:
# 		print("Issue : ", e)