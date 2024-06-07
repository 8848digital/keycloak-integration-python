import frappe

@frappe.whitelist()
def map_groups_in_frappe(kwargs):
	if kwargs["operation"] == "create":
		create_group_mapping(kwargs)
	elif kwargs["operation"] == "delete":
		delete_group_mapping(kwargs)
	
def create_group_mapping(kwargs):
	print("CHECK")
	if kwargs.get("parent"):
		try:
			print("1")
			doc = frappe.get_doc("Keycloak Erpnext Group Mapping","Module Profile")
			module_profile_data = doc.append("module_profile_details",{})
			module_profile_data.module_name = kwargs["group_details"]["name"]
			module_profile_data.module_id = kwargs["group_details"]["id"]
			doc.save(ignore_permissions=True)
		except Exception as e:
			print("Issue : ", e)
	else:
		try:
			print("*************************************************")
			print("2")
			print("Parent not found")
			doc = frappe.new_doc("Keycloak Erpnext Group Mapping")
			doc.group_id = kwargs["group_details"]["id"]
			doc.group_name = kwargs["group_details"]["name"]
			doc.save(ignore_permissions=True)
		except Exception as e:
			print("Issue",e)
	
def delete_group_mapping(kwargs):
	print("SUCCESS")
	print("kwargs : ",kwargs)
	try:
		module_profile_data = [] 
		doc = frappe.get_doc("Keycloak Erpnext Group Mapping","Module Profile")
		for row in doc.module_profile_details:
			# print("ROW MODULE NAME : ",row.module_id, " , DOC NAME : ",doc.module_profile_id)
			if row.module_id != kwargs["module_profile_id"]:
				print("I")
				# delete the child table row
				row_data = {
					"module_name": row.module_name,
                    "module_id": row.module_id
				}
				module_profile_data.append(row_data)

		doc.module_profile_details = []    

		print(module_profile_data)
		for row in module_profile_data:
			doc.append("module_profile_details",row)
		doc.save(ignore_permissions=True)

	except Exception as e:
		print("Issue : ", e)