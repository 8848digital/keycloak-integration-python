// Copyright (c) 2026 8848 Digital LLP. All rights reserved.
// Proprietary and confidential. Unauthorized copying, distribution, or use
// of this file, via any medium, is strictly prohibited without prior
// written permission from 8848 Digital LLP.

frappe.ui.form.on("Permission Type", {
	/**
	 * Set the row pickers and the read-only state of each row.
	 *
	 * @param {object} frm - The current form.
	 * @returns {void}
	 */
	refresh(frm) {
		set_allow_doctype_filter(frm);

		frm.set_query("applicable_for", "permission_type_doctype", (doc, cdt, cdn) => ({
			query: "frappe.core.doctype.user_permission.user_permission.get_applicable_for_doctype_list",
			doctype: locals[cdt][cdn].allow_doctype,
		}));

		(frm.doc.permission_type_doctype || []).forEach((row) => {
			set_row_field_read_only(frm, row, "hide_descendants", !is_nested_set_doctype(row));
			set_row_field_read_only(frm, row, "applicable_for", row.apply_to_all_doctypes === 1);
		});
	},
});

frappe.ui.form.on("Permission Type Doctype", {
	/**
	 * Refresh the picker filter and the row state when the DocType changes.
	 *
	 * @param {object} frm - The current form.
	 * @param {string} cdt - The child DocType.
	 * @param {string} cdn - The child row name.
	 * @returns {void}
	 */
	allow_doctype(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		set_allow_doctype_filter(frm);
		set_row_field_read_only(frm, row, "hide_descendants", !is_nested_set_doctype(row));
		if (row.applicable_for) {
			frappe.model.set_value(cdt, cdn, "applicable_for", null);
		}
	},

	/**
	 * "Apply to all" and "Applicable for" exclude each other.
	 *
	 * @param {object} frm - The current form.
	 * @param {string} cdt - The child DocType.
	 * @param {string} cdn - The child row name.
	 * @returns {void}
	 */
	apply_to_all_doctypes(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		set_row_field_read_only(frm, row, "applicable_for", row.apply_to_all_doctypes === 1);
		if (row.apply_to_all_doctypes === 1 && row.applicable_for) {
			frappe.model.set_value(cdt, cdn, "applicable_for", null);
		}
	},

	/**
	 * Reject "Applicable for" while "Apply to all" is set.
	 *
	 * @param {object} frm - The current form.
	 * @param {string} cdt - The child DocType.
	 * @param {string} cdn - The child row name.
	 * @returns {void}
	 */
	applicable_for(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.apply_to_all_doctypes === 1 && row.applicable_for) {
			frappe.model.set_value(cdt, cdn, "applicable_for", null);
			frappe.throw(__("Uncheck the apply_to_all_document_types checkbox first"));
		}
	},
});

/**
 * Check whether "Hide Descendants" applies to the row's DocType (tree DocTypes only).
 *
 * @param {object} row - A Permission Type Doctype row.
 * @returns {boolean} True for a nested-set DocType.
 */
function is_nested_set_doctype(row) {
	return (frappe.boot.nested_set_doctypes || []).includes(row.allow_doctype);
}

/**
 * Set one field of one grid row to read only or editable.
 *
 * @param {object} frm - The current form.
 * @param {object} row - The child row.
 * @param {string} fieldname - The field to change.
 * @param {boolean} read_only - True to make the field read only.
 * @returns {void}
 */
function set_row_field_read_only(frm, row, fieldname, read_only) {
	const grid_row = frm.fields_dict.permission_type_doctype.grid.grid_rows_by_docname[row.name];
	if (grid_row) {
		grid_row.set_field_property(fieldname, "read_only", read_only ? 1 : 0);
	}
}

/**
 * Hide DocTypes that already have a row, plus single and child DocTypes.
 *
 * @param {object} frm - The current form.
 * @returns {void}
 */
function set_allow_doctype_filter(frm) {
	const selected = (frm.doc.permission_type_doctype || [])
		.map((row) => row.allow_doctype)
		.filter(Boolean);

	frm.set_query("allow_doctype", "permission_type_doctype", () => ({
		filters: { issingle: 0, istable: 0, name: ["not in", selected] },
	}));
}
