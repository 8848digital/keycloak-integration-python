// Copyright (c) 2024, Amandeep and contributors
// For license information, please see license.txt

frappe.ui.form.on('User and Permission Configuration', {
	refresh: function(frm) {
		frm.set_query("doc_type", "user_permission_doctype_value", function () {
			return {
				query: "keycloak.keycloak_integration.doctype.user_and_permission_configuration.user_and_permission_configuration.filter_doctypes_based_on_permissions",
				filters: { permission_type: frm.doc.permission_type },
			}
		});
	}
});
