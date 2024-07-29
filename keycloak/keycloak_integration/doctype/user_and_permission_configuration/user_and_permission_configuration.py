# Copyright (c) 2024, Amandeep and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class UserandPermissionConfiguration(Document):
	def before_save(self):
		self.create_user_permissions()


	def create_user_permissions(self):
		previous_permission_type = frappe.get_value(self.doctype, self.name, pluck = "name")
		previous_permission_type_doctypes = frappe.get_all("Permission Type Doctype", filters={"parent": previous_permission_type}, fields = ["allow_doctype", "apply_to_all_document_types", "applicable_for", "hide_descendants", "is_default"])
		previous_records = frappe.get_all("User Permission Doctype Value", filters = {"parent": self.name}, fields = ["doc_type", "value"])
		previous_configs = self.create_config(previous_permission_type_doctypes, previous_records)

		current_permission_type_doctypes = previous_permission_type_doctypes
		current_records = self.user_permission_doctype_value
		current_configs = self.create_config(current_permission_type_doctypes, current_records)

		

		
	def create_config(self, config_doctypes, records):
		config_doctype_map = {}
		for config_doctype in config_doctypes:
			config_doctype_map[config_doctype.get("allow_doctype")] = config_doctype
		configs = []
		for record in records:
			config = {"value": record.get("value")}
			config.update(config_doctype_map.get(record.get("doc_type")))
			configs.append(config)
		return configs





		user_permission_records = []
		doctype_list = []
		for doctype in self.user_permission_doctype_value:
			user_permission_record = {
				"doctype": "User Permission",
				"user": self.user,
				"allow": doctype.doc_type,
				"for_value": doctype.value
			}
			user_permission_records.append(user_permission_record)
			doctype_list.append(doctype.doc_type)
		doctype_details = frappe.get_all("Permission Type Doctype", filters={"parent": self.permission_type, "allow_doctype": ["In", doctype_list]}, fields = ["allow_doctype", "apply_to_all_document_types", "applicable_for", "hide_descendants", "is_default"])
		doctype_details_map = {}
		for doctype_detail in doctype_details:
			doctype_details_map[doctype_detail.allow_doctype] = doctype_detail
		for record in user_permission_records:
			doctype_detail = doctype_details_map.get(record.get("allow")) or {}
			if doctype_detail:
				record.update(doctype_detail)
				record.update({"apply_to_all_doctypes": doctype_detail.get("apply_to_all_document_types")})
				frappe.get_doc(record).insert()

@frappe.whitelist()
def filter_doctypes_based_on_permissions(doctype, txt, searchfield, start, page_len, filters):
	permission_type = filters.get("permission_type")
	if permission_type:
		filtered_doctypes = f"""
			SELECT child.allow_doctype
			FROM `tabPermission Type Doctype` as child
			JOIN `tabPermission Type` as parent
			ON child.parent = parent
			WHERE parent.name1 = "{permission_type}"
		"""
		print(frappe.db.sql(filtered_doctypes))
		return frappe.db.sql(filtered_doctypes)
	else:
		return []
