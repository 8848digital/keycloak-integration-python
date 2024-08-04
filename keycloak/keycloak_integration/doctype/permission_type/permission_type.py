# Copyright (c) 2024, Amandeep and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

class PermissionType(Document):
	def validate(self):
		self.validate_doctype_entry()
		self.validate_doctype_links()

	def validate_doctype_entry(self):
		present_doctype = []
		for row in self.permission_type_doctype:
			if row.allow_doctype in present_doctype:
				frappe.throw(_("Only Single Entry For A Doctype is Allowed: "+ row.allow_doctype))
			else:
				present_doctype.append(row.allow_doctype)
	
	def validate_doctype_links(self):
		previous_entries = frappe.get_all("Permission Type Doctype", filters = {"parent": self.name,}, fields = ["allow_doctype", "apply_to_all_doctypes", "applicable_for", "hide_descendants", "is_default"])
		current_entries = self.permission_type_doctype
		non_matching_entries = []
		for previous_entry in previous_entries:
			if not any(is_dict_match(previous_entry, current_entry) for current_entry in current_entries):
				non_matching_entries.append(previous_entry)
		for entry in non_matching_entries:
			entry_links = self.check_doctype_link(entry)
			if entry_links:
				frappe.throw(_(f"Cannot update/remove config {str(entry)} as it is already linked to User and Permission Configuration: {entry_links}"))

	def check_doctype_link(self, entry):
		entry_links = frappe.db.sql("""SELECT upc.name 
						FROM `tabUser and Permission Configuration` as upc
						JOIN `tabUser Permission Doctype Value` as updc
						ON updc.parent = upc.name
						WHERE upc.permission_type = %s
						AND updc.allow_doctype = %s
						AND updc.apply_to_all_doctypes = %s
						AND updc.applicable_for = %s
						AND updc.hide_descendants = %s
						AND updc.is_default = %s
						""", (self.name, 
							entry.get("allow_doctype"), 
							entry.get("apply_to_all_doctypes"), 
							entry.get("applicable_for"),
							entry.get("hide_descendants"), 
							entry.get("is_default")), as_dict=1)
		return entry_links
		

def is_dict_match(previous_entry, current_entry):
	return all(current_entry.get(key) == value for key, value in previous_entry.items()) 