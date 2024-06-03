import frappe

@frappe.whitelist()
def map_groups_in_frappe(kwargs):
	if kwargs["operation"] == "create":
		create_group_mapping(kwargs)
	elif kwargs["operation"] == "delete":
		pass
	print("PYTHON GROUPS")
	print(kwargs)
	
def create_group_mapping(kwargs):
	try:
		doc = frappe.new_doc("Keycloak Erpnext Group Mapping")
		doc.group_id = kwargs["group_details"]["id"]
		doc.group_name = kwargs["group_details"]["name"]
		doc.save(ignore_permissions=True)
	except Exception as e:
		print("Issue : ", e)