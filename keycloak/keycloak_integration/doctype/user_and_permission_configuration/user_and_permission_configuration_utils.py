# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.

"""Create and delete User Permission records for a configuration."""

import frappe
from frappe import _

ROW_DOCTYPE = "User Permission Doctype Value"
PERMISSION_TYPE_ROW_DOCTYPE = "Permission Type Doctype"
CONFIG_FIELDS = ("allow_doctype", "apply_to_all_doctypes", "applicable_for", "hide_descendants", "is_default")


def validate_permission_type_doctypes(doc):
	"""
	Throw when a row uses a DocType that is not in the Permission Type.

	Parameters:
		doc (Document, required): The User and Permission Configuration.

	Returns:
		None
	"""
	allowed_doctypes = frappe.get_all(
		PERMISSION_TYPE_ROW_DOCTYPE, filters={"parent": doc.permission_type}, pluck="allow_doctype"
	)
	for row in doc.user_permission_doctype_value:
		if row.doc_type not in allowed_doctypes:
			frappe.throw(
				_('row {0}: Doctype "{1}" not present in Permission Type "{2}"').format(
					row.idx, row.doc_type, doc.permission_type
				)
			)


def sync_user_permissions(doc):
	"""
	Compare the saved rows with the rows being saved, then delete the User
	Permissions that are no longer wanted and create the new ones.

	Parameters:
		doc (Document, required): The User and Permission Configuration.

	Returns:
		None
	"""
	previous_user = frappe.db.get_value(doc.doctype, doc.name, "user")
	previous_rows = frappe.get_all(
		ROW_DOCTYPE,
		filters={"parent": doc.name, "parenttype": doc.doctype},
		fields=["for_value", "user_permission_record", "doc_type", *CONFIG_FIELDS],
	)
	previous_configs = create_config(previous_rows, previous_rows, previous_user)

	permission_type_rows = frappe.get_all(
		PERMISSION_TYPE_ROW_DOCTYPE, filters={"parent": doc.permission_type}, fields=list(CONFIG_FIELDS)
	)
	current_configs = create_config(permission_type_rows, doc.user_permission_doctype_value, doc.user)

	configs_to_remove, configs_to_add = compare_configs(previous_configs, current_configs)
	remove_user_permission_records(configs_to_remove)
	create_user_permission_records(doc, configs_to_add)


def create_user_permission_records(doc, configs_to_add):
	"""
	Insert one User Permission per config and store its name on the row.

	Parameters:
		doc (Document, required): The User and Permission Configuration.
		configs_to_add (list[dict], required): Output of compare_configs.

	Returns:
		None
	"""
	for config in configs_to_add:
		try:
			user_permission = frappe.get_doc({"doctype": "User Permission", **config}).insert()
		except Exception as error:
			frappe.throw(_("{0} for config {1}").format(error, config))

		row_values = {key: value for key, value in config.items() if key != "allow"}
		row_values["user_permission_record"] = user_permission.name
		for row in doc.user_permission_doctype_value:
			if row.doc_type == config.get("allow_doctype") and str(row.for_value) == config.get("for_value"):
				row.update(row_values)


def remove_user_permission_records(configs_to_remove):
	"""
	Delete the User Permission records of the given configs.

	Parameters:
		configs_to_remove (list[dict], required): Output of compare_configs.

	Returns:
		None
	"""
	for config in configs_to_remove:
		if not config.get("user_permission_record"):
			continue

		try:
			delete_user_permission(config["user_permission_record"])
		except Exception as error:
			frappe.throw(_("{0} for config {1}").format(error, config))


def delete_user_permission_records(doc):
	"""
	Delete every User Permission record linked from the configuration rows.

	Parameters:
		doc (Document, required): The User and Permission Configuration.

	Returns:
		None
	"""
	for row in doc.user_permission_doctype_value:
		if row.user_permission_record:
			delete_user_permission(row.user_permission_record)

	frappe.msgprint(_("User Permission Deleted Successfully"))


def delete_user_permission(name):
	"""
	Delete one User Permission, flagged so the User Permission on_trash
	guard knows the configuration itself requested it.

	Parameters:
		name (str, required): The User Permission name.

	Returns:
		None
	"""
	if not frappe.db.exists("User Permission", name):
		return

	user_permission = frappe.get_doc("User Permission", name)
	user_permission.flags.upc_delete_request = 1
	user_permission.delete()


def create_config(config_rows, records, user):
	"""
	Build one comparable config dict per record whose DocType is configured.

	Parameters:
		config_rows (list[dict], required): Rows with CONFIG_FIELDS, keyed by allow_doctype.
		records (list, required): Configuration rows with doc_type, for_value
			and user_permission_record.
		user (str, optional): The user the permissions are for.

	Returns:
		list[dict]: Configs that include "allow" (the User Permission DocType).
	"""
	config_by_doctype = {
		row.get("allow_doctype"): {field: row.get(field) for field in CONFIG_FIELDS} for row in config_rows
	}

	configs = []
	for record in records:
		doctype_config = config_by_doctype.get(record.get("doc_type"))
		if not doctype_config:
			continue

		config = {
			"user": user,
			"for_value": record.get("for_value"),
			"user_permission_record": record.get("user_permission_record"),
			**doctype_config,
		}
		config["allow"] = config["allow_doctype"]
		configs.append(config)

	return configs


def compare_configs(previous_configs, current_configs):
	"""
	Work out which configs to remove and which to add.

	Parameters:
		previous_configs (list[dict], required): Configs of the saved rows.
		current_configs (list[dict], required): Configs of the rows being saved.

	Returns:
		tuple[list[dict], list[dict]]: (to_remove, to_add)
	"""
	previous_set = {__to_tuple(config) for config in previous_configs}
	current_set = {__to_tuple(config) for config in current_configs}
	return [dict(item) for item in previous_set - current_set], [dict(item) for item in current_set - previous_set]


def __to_tuple(config):
	"""
	Make a config hashable. Numbers become strings, because the saved rows
	store the check values in Data fields.

	Parameters:
		config (dict, required): One config.

	Returns:
		tuple: Sorted (key, value) pairs.
	"""
	return tuple(
		sorted((key, str(value) if isinstance(value, int | float) else value) for key, value in config.items())
	)
