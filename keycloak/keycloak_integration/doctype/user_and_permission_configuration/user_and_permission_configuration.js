// Copyright (c) 2026 8848 Digital LLP. All rights reserved.
// Proprietary and confidential. Unauthorized copying, distribution, or use
// of this file, via any medium, is strictly prohibited without prior
// written permission from 8848 Digital LLP.

frappe.ui.form.on("User and Permission Configuration", {
	/**
	 * Limit the row DocType picker to the selected Permission Type.
	 *
	 * @param {object} frm - The current form.
	 * @returns {void}
	 */
	refresh(frm) {
		frm.set_query("doc_type", "user_permission_doctype_value", () => ({
			query: "keycloak.keycloak_integration.api.v1.user_and_permission_configuration.filter_doctypes_based_on_permissions",
			filters: { permission_type: frm.doc.permission_type },
		}));
	},
});

frappe.ui.form.on("User Permission Doctype Value", {
	/**
	 * Clear the value when the row's DocType changes, because it links to the old DocType.
	 *
	 * @param {object} frm - The current form.
	 * @param {string} cdt - The child DocType.
	 * @param {string} cdn - The child row name.
	 * @returns {void}
	 */
	doc_type(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.for_value) {
			frappe.model.set_value(cdt, cdn, "for_value", null);
		}
	},
});
