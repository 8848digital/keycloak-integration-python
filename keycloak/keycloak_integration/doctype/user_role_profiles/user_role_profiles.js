// Copyright (c) 2026 8848 Digital LLP. All rights reserved.
// Proprietary and confidential. Unauthorized copying, distribution, or use
// of this file, via any medium, is strictly prohibited without prior
// written permission from 8848 Digital LLP.

frappe.ui.form.on("User Role Profiles", {
	refresh: function (frm) {
		frm.set_df_property("role_profiles", "cannot_add_rows", true);
		frm.set_df_property("role_profiles", "cannot_delete_rows", true);
	},
});
