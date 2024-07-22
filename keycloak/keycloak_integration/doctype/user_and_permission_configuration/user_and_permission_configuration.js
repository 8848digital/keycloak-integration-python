// Copyright (c) 2024, Amandeep and contributors
// For license information, please see license.txt

frappe.ui.form.on('User and Permission Configuration', {
	refresh: function(frm) {
		frm.set_query("doc_type", "user_permission_doctype_value", function () {
			return {
				filters: {
					issingle: 0,
					istable: 0
				},
			}
		});
	}
});
