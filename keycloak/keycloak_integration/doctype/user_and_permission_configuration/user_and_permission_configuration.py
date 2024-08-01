# Copyright (c) 2024, Amandeep and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class UserandPermissionConfiguration(Document):
	pass
	def before_save(self):
		self.create_user_permissions()

	def create_user_permissions(self):
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
			FROM `tabPermission Type` as parent
			LEFT JOIN `tabPermission Type Doctype` as child
			ON child.parent = parent.name
			WHERE parent.name = "{permission_type}" 
		"""
		print(frappe.db.sql(filtered_doctypes))
		return frappe.db.sql(filtered_doctypes)
	else:
		return []
