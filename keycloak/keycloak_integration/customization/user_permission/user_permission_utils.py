# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.

"""Protect User Permissions that a "User and Permission Configuration" owns."""

import frappe
from frappe import _
from frappe.utils import escape_html, get_url_to_form

CONFIGURATION_DOCTYPE = "User and Permission Configuration"
CONFIGURATION_ROW_DOCTYPE = "User Permission Doctype Value"


def validate_not_linked_to_configuration(doc):
	"""
	Block deleting a User Permission that a configuration created, unless
	the configuration itself is removing it (flags.upc_delete_request).

	Parameters:
		doc (Document, required): The User Permission being deleted.

	Returns:
		None

	Raises:
		frappe.ValidationError: When a configuration still links to it.
	"""
	if doc.flags.upc_delete_request:
		return

	configuration = frappe.db.get_value(
		CONFIGURATION_ROW_DOCTYPE,
		{"user_permission_record": doc.name, "parenttype": CONFIGURATION_DOCTYPE},
		"parent",
	)
	if not configuration:
		return

	link = get_url_to_form(CONFIGURATION_DOCTYPE, configuration)
	frappe.throw(
		_("Cannot delete the record as it is linked with {0}").format(
			f"<a href='{escape_html(link)}'>{escape_html(configuration)}</a>"
		)
	)
