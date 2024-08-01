# Copyright (c) 2024, Amandeep and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

class PermissionType(Document):
	def validate(self):
		present_doctype = []
		for row in self.permission_type_doctype:
			if row.allow_doctype in present_doctype:
				frappe.throw(_("Only Single Entry For A Doctype is Allowed: "+ row.allow_doctype))
			else:
				present_doctype.append(row.allow_doctype)