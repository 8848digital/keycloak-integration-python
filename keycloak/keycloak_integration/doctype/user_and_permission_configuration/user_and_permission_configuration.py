# Copyright (c) 2024, Amandeep and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class UserandPermissionConfiguration(Document):
	pass

@frappe.whitelist()
def filter_doctypes_based_on_permissions(doctype, txt, searchfield, start, page_len, filters):
	print("1")
	permission_type = filters.get("permission_type")
	print(permission_type)
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
