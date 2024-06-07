import frappe

@frappe.whitelist()
def map_groups_in_frappe(kwargs):
	if kwargs["operation"] == "create":
		create_group_mapping(kwargs)
	elif kwargs["operation"] == "delete":
		delete_group_mapping(kwargs)
	
def create_group_mapping(kwargs):
	if kwargs.get("parent"):
		update_module_profile_map(kwargs)
	else:
		create_new_group_map(kwargs)
	
def delete_group_mapping(kwargs):
	try:
		module_profile_data = [] 
		doc = frappe.get_doc("Keycloak Erpnext Group Mapping","Module Profile")
		for row in doc.module_profile_details:
			if row.module_id != kwargs["module_profile_id"]:
				# delete the child table row
				row_data = {
					"module_name": row.module_name,
                    "module_id": row.module_id
				}
				module_profile_data.append(row_data)

		doc.module_profile_details = []    
		for row in module_profile_data:
			doc.append("module_profile_details",row)
		doc.save(ignore_permissions=True)
	except Exception as e:
		print("Issue : ", e)

def update_module_profile_map(kwargs):
	try:
		doc = frappe.get_doc("Keycloak Erpnext Group Mapping","Module Profile")
		module_profile_data = doc.append("module_profile_details",{})
		module_profile_data.module_name = kwargs["group_details"]["name"]
		module_profile_data.module_id = kwargs["group_details"]["id"]
		doc.save(ignore_permissions=True)
	except Exception as e:
		print("Issue : ", e)

def create_new_group_map(kwargs):
	try:
		doc = frappe.new_doc("Keycloak Erpnext Group Mapping")
		doc.group_id = kwargs["group_details"]["id"]
		doc.group_name = kwargs["group_details"]["name"]
		doc.save(ignore_permissions=True)
	except Exception as e:
		print("Issue",e)