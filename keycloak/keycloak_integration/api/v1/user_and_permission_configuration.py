# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.

"""Desk helpers for the User and Permission Configuration form."""

import frappe


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def filter_doctypes_based_on_permissions(doctype, txt, searchfield, start, page_len, filters):
	"""
	Link-field search query: list only the DocTypes of the selected
	Permission Type, so the user cannot pick an unsupported DocType.

	**Endpoint:** `/api/method/keycloak.keycloak_integration.api.v1.user_and_permission_configuration.filter_doctypes_based_on_permissions`
	(called by Desk's link search through `frappe.desk.search.search_widget`)
	**HTTP Method:** GET / POST
	**Parameters:**
		- doctype (str, required): The linked DocType ("DocType").
		- txt (str, required): The text typed in the link field.
		- searchfield (str, required): Ignored.
		- start (int, required): Offset for paging.
		- page_len (int, required): Page size.
		- filters (dict, required): Needs "permission_type".
	**Response:**
	```json
	{"message": [["Customer"], ["Company"]]}
	```
	"""
	permission_type = (filters or {}).get("permission_type")
	if not permission_type or not frappe.has_permission("Permission Type", "read", permission_type):
		return []

	row = frappe.qb.DocType("Permission Type Doctype")
	return (
		frappe.qb.from_(row)
		.select(row.allow_doctype)
		.where(row.parenttype == "Permission Type")
		.where(row.parent == permission_type)
		.where(row.allow_doctype.like(f"%{txt}%"))
		.orderby(row.idx)
		.limit(page_len)
		.offset(start)
	).run()
