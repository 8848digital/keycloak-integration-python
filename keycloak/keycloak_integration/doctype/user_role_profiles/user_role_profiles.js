// Copyright (c) 2024, Amandeep and contributors
// For license information, please see license.txt

frappe.ui.form.on('User Role Profiles', {
	refresh: function(frm) {
		frm.set_df_property("role_profiles","cannot_add_rows",true);
		frm.set_df_property("role_profiles","cannot_delete_rows",true);
	}
});
