# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.

"""Validation logic for the Permission Type DocType."""

import frappe
from frappe import _

# Fields that together define one Permission Type row.
ROW_FIELDS = (
	"allow_doctype",
	"apply_to_all_doctypes",
	"applicable_for",
	"hide_descendants",
	"is_default",
)


def validate_unique_doctypes(doc):
	"""
	Allow each DocType only once per Permission Type.

	Parameters:
	        doc (Document, required): The Permission Type.

	Returns:
	        None
	"""
	seen = set()
	for row in doc.permission_type_doctype:
		if row.allow_doctype in seen:
			frappe.throw(_("Only Single Entry For A Doctype is Allowed: {0}").format(row.allow_doctype))

		seen.add(row.allow_doctype)


def validate_row_options(doc):
	"""
	Enforce the form's rules on the server too, so API calls and imports
	cannot save contradictory rows: "Applicable For" needs "Apply To All
	Doctypes" off, and "Hide Descendants" only works for tree DocTypes.

	Parameters:
	        doc (Document, required): The Permission Type.

	Returns:
	        None
	"""
	for row in doc.permission_type_doctype:
		if row.applicable_for and row.apply_to_all_doctypes:
			frappe.throw(_("Row {0}: uncheck Apply To All Doctypes to set Applicable For").format(row.idx))

		if row.hide_descendants and not frappe.get_meta(row.allow_doctype).is_nested_set():
			frappe.throw(
				_("Row {0}: Hide Descendants is only allowed for tree DocTypes, not {1}").format(
					row.idx, row.allow_doctype
				)
			)


def validate_doctype_links(doc):
	"""
	Block changing or removing a saved row while a User and Permission
	Configuration still uses it.

	Parameters:
	        doc (Document, required): The Permission Type.

	Returns:
	        None
	"""
	previous_rows = frappe.get_all(
		"Permission Type Doctype", filters={"parent": doc.name}, fields=list(ROW_FIELDS)
	)
	for previous_row in previous_rows:
		if any(is_dict_match(previous_row, row) for row in doc.permission_type_doctype):
			continue

		linked_configurations = get_linked_configurations(doc.name, previous_row)
		if linked_configurations:
			frappe.throw(
				_(
					"Cannot update/remove config {0} as it is already linked to User and Permission Configuration: {1}"
				).format(previous_row, ", ".join(linked_configurations))
			)


def get_linked_configurations(permission_type, row):
	"""
	Find the configurations that use one Permission Type row.

	Parameters:
	        permission_type (str, required): The Permission Type name.
	        row (dict, required): The row values (see ROW_FIELDS).

	Returns:
	        list[str]: Names of linked User and Permission Configurations.
	"""
	configuration = frappe.qb.DocType("User and Permission Configuration")
	value = frappe.qb.DocType("User Permission Doctype Value")
	query = (
		frappe.qb.from_(configuration)
		.join(value)
		.on(value.parent == configuration.name)
		.select(configuration.name)
		.distinct()
		.where(configuration.permission_type == permission_type)
	)
	for fieldname in ROW_FIELDS:
		query = query.where(value[fieldname] == row.get(fieldname))

	return query.run(pluck=True)


def is_dict_match(previous_row, current_row):
	"""
	Check that every value of a saved row is unchanged in the current row.

	Parameters:
	        previous_row (dict, required): The saved row values.
	        current_row (Document | dict, required): The row being saved.

	Returns:
	        bool: True when all values match.
	"""
	return all(current_row.get(key) == value for key, value in previous_row.items())
