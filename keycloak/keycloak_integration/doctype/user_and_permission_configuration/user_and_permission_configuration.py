# Copyright (c) 2024, Amandeep and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

class UserandPermissionConfiguration(Document):
	def validate(self):
		self.validate_permission_type_doctype()

	def before_save(self):
		self.create_user_permissions()

	def after_delete(self):
		print("after delete activate")
		self.delete_user_permission_records()

	def validate_permission_type_doctype(self):
		permission_type_doctypes = frappe.get_all("Permission Type Doctype", filters={"parent": self.permission_type}, fields = ["allow_doctype"], pluck = "allow_doctype")
		for record in self.user_permission_doctype_value:
			if record.doc_type not in permission_type_doctypes:
				frappe.throw(f'row {record.idx}: Doctype "{record.doc_type}" not present in Permission Type "{self.permission_type}"')
	
	def create_user_permissions(self):
		previous_user = frappe.get_value(self.doctype, self.name, "user")
		previous_records = frappe.get_all("User Permission Doctype Value", filters = {"parent": self.name}, fields = ["for_value", "user_permission_record", "allow_doctype", "apply_to_all_doctypes", "applicable_for", "hide_descendants", "is_default", "doc_type"])
		print("Previous Records : ",previous_records)
		print("..............................................................")
		
		previous_configs = create_config(previous_records, previous_records, previous_user)

		current_permission_type_doctypes = frappe.get_all("Permission Type Doctype", filters={"parent": self.permission_type}, fields = ["allow_doctype", "apply_to_all_doctypes", "applicable_for", "hide_descendants", "is_default"])
		current_records = self.user_permission_doctype_value
		current_configs = create_config(current_permission_type_doctypes, current_records, self.user)

		print("Current config : ",current_configs)
		print("Previous config : ",previous_configs)
		print("....................................................")

		configs_to_remove, configs_to_add = compare_configs(previous_configs, current_configs)
		print("Configs to add " ,configs_to_add)
		print("Configs to remove " ,configs_to_remove)
		self.remove_user_permission_record(configs_to_remove) 
		self.create_user_permission_record(configs_to_add)

	def create_user_permission_record(self, configs_to_add):
		for config in configs_to_add:
			# if not config.get("user_permission_record"):
			record = {"doctype": "User Permission"}
			record.update(config)
			try:
				record["user_permission_record"] = frappe.get_doc(record).insert().name
				del record["doctype"]
				del record["allow"]
				for row in self.user_permission_doctype_value:
					if row.doc_type == record.get("allow_doctype") and str(row.for_value) == record.get("for_value"):
						row.update(record)
			except Exception as e:
				frappe.throw(str(e)+" for config "+ str(config))
	
	def remove_user_permission_record(self, configs_to_remove):
		for config in configs_to_remove:
			user_permission_record = config.get("user_permission_record")
			print(user_permission_record)
			if user_permission_record:
				try:
					doc = frappe.get_doc("User Permission", user_permission_record)
					print(doc)
					doc.flags.upc_delete_request = 1
					doc.delete()
				except Exception as e:
					frappe.throw(str(e)+" for config "+ str(config))
	
	def delete_user_permission_records(self):
		try:
			# doc = frappe.get_doc("User and Permission Configuration",self.name)
			for row in self.user_permission_doctype_value:
				print()
				doc = frappe.get_doc("User Permission",row.user_permission_record)
				doc.flags.upc_delete_request = 1
				doc.delete()
			frappe.msgprint(_("User Permission Deleted Successfully"))
		except Exception as e:
			print(e," :Error")
			frappe.throw(_("Error : ", e))


def dict_to_tuple(d):
		"""Convert a dictionary to a sorted tuple of key-value pairs."""
		return tuple(sorted(d.items()))

def compare_configs(prev_config, current_config):
	prev_config_normalized = [normalize_dict(d) for d in prev_config]
	current_config_normalized = [normalize_dict(d) for d in current_config]
	"""Compare previous and current configuration lists to determine what to remove and add."""
	# Convert lists of dicts to sets of tuples
	prev_set = set(dict_to_tuple(d) for d in prev_config_normalized)
	current_set = set(dict_to_tuple(d) for d in current_config_normalized)
	print(prev_set)
	print(current_set)
	
	# Determine items to remove and add
	to_remove = prev_set - current_set
	to_add = current_set - prev_set
	
	# Convert tuples back to dictionaries
	to_remove_list = [dict(t) for t in to_remove]
	to_add_list = [dict(t) for t in to_add]
	
	return to_remove_list, to_add_list
	

def create_config(config_doctypes, records, user):
	config_doctype_map = {}
	for config_doctype in config_doctypes:
		config_doctype_map[config_doctype.get("allow_doctype")] = {"allow_doctype":config_doctype.get("allow_doctype"),
															 "apply_to_all_doctypes":config_doctype.get("apply_to_all_doctypes"),
															"applicable_for":config_doctype.get("applicable_for"),
															"hide_descendants":config_doctype.get("hide_descendants"),
															"is_default":config_doctype.get("is_default")}
	print(config_doctype_map, "jrgghugh")
	configs = []
	for record in records:
		if config_doctype_map.get(record.get("doc_type")):
			config = {
						"user": user,
						"for_value": record.get("for_value"),
						"user_permission_record": record.get("user_permission_record")
					}
			config.update(config_doctype_map.get(record.get("doc_type")) or {})
			config["allow"] = config.get("allow_doctype")
			print(config)
			configs.append(config)	
	return configs

def normalize_dict(d):
    """Normalize dictionary values to ensure consistent types for comparison."""
    normalized_dict = {}
    for k, v in d.items():
        # Convert values to string for consistent comparison
        if isinstance(v, (int, float)):
            normalized_dict[k] = str(v)
        else:
            normalized_dict[k] = v
    return normalized_dict

@frappe.whitelist()
def filter_doctypes_based_on_permissions(doctype, txt, searchfield, start, page_len, filters):
	permission_type = filters.get("permission_type")
	if permission_type:
		permission_type_parent = frappe.qb.DocType('Permission Type')
		permission_type_child = frappe.qb.DocType('Permission Type Doctype')
		query = (
			frappe.qb.from_(permission_type_parent)
			.left_join(permission_type_child)
			.on(permission_type_child.parent == permission_type_parent.name)
			.select(permission_type_child.allow_doctype)
			.where(permission_type_parent.name == permission_type)
		).run()		
		return query
	else:
		return []