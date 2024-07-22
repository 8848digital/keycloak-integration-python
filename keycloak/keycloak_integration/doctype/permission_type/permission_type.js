// Copyright (c) 2024, Amandeep and contributors
// For license information, please see license.txt

frappe.ui.form.on('Permission Type', {
	// refresh: function(frm) {

	// }
});

frappe.ui.form.on('Permission Type Doctype', {
	apply_to_all_document_types: function(frm,cdt,cdn) {
		var child = locals[cdt][cdn];
		set_applicable_for_read_only(child);	
	},
	applicable_for: function(frm,cdt,cdn) {
		var child = locals[cdt][cdn];
		if (child.apply_to_all_document_types === 1) {
			child.applicable_for = null;
			frm.refresh_field("permission_type_doctype");
			frappe.throw(__("Uncheck the apply_to_all_document_types checkbox first"));
		}
	}
});

function set_applicable_for_read_only(child) {
	if (child.apply_to_all_document_types === 1) {
		cur_frm.fields_dict["permission_type_doctype"].grid.grid_rows_by_docname[child.name].set_field_property('applicable_for','read_only',1);
	} else {
		cur_frm.fields_dict["permission_type_doctype"].grid.grid_rows_by_docname[child.name].set_field_property('applicable_for','read_only',0);
	}
}