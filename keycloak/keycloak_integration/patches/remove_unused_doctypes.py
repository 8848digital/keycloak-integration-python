# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.

"""Delete the DocTypes left over from the old push-sync design."""

import frappe

# Replaced by Frappe's standard "User Social Login" link and by the
# real-time listener, which no longer mirrors groups.
UNUSED_DOCTYPES = (
	"Erpnext Keycloak User Mapping",
	"Module Profile Name",
	"Keycloak Erpnext Group Mapping",
)


def execute():
	"""
	Drop the unused DocTypes and their tables. Child table first, so the
	parent DocType has no remaining link to it.

	Returns:
	        None
	"""
	for doctype in UNUSED_DOCTYPES:
		if frappe.db.exists("DocType", doctype):
			frappe.delete_doc("DocType", doctype, force=True, ignore_missing=True)

		# delete_doc keeps the table of an app DocType; drop it explicitly.
		frappe.db.sql_ddl(f"DROP TABLE IF EXISTS `tab{doctype}`")
