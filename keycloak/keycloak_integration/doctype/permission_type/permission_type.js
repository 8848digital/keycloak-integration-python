// Copyright (c) 2024, Amandeep and contributors
// For license information, please see license.txt

frappe.ui.form.on('Permission Type', {
	refresh: function(frm) {
		set_allow_doctype_filter(frm);
		frm.set_query("allow_doctype", "permission_type_doctype", function (doc,cdt,cdn) {
			return {
					filters: {
						issingle: 0,
						istable: 0
					},
				}
		});

		frm.set_query("applicable_for", "permission_type_doctype", function (doc,cdt,cdn) {
			var row = locals[cdt][cdn];
			return {
				query: "frappe.core.doctype.user_permission.user_permission.get_applicable_for_doctype_list",
				doctype: row.allow_doctype
			};
		});

		// set the hide descendants checkbox read only
		frm.doc.permission_type_doctype.forEach(row => {
			var hide_descendants_checkbox = toggle_hide_descendants(row);
			if (hide_descendants_checkbox) {
				frm.fields_dict.permission_type_doctype.grid.grid_rows[row.idx-1].docfields[3].read_only=0
				frm.refresh_field("permission_type_doctype")
			}
		})
	}
});

frappe.ui.form.on('Permission Type Doctype', {
	allow_doctype: function(frm,cdt,cdn) {
		set_allow_doctype_filter(frm);

		var child = locals[cdt][cdn];
		var hide_descendants_checkbox = toggle_hide_descendants(child);
		set_hide_descendants_checkbox_read_only(child, hide_descendants_checkbox);	
		if (child.applicable_for) {
			child.applicable_for = null;
			frm.refresh_field("permission_type_doctype");
		}
	},
	apply_to_all_doctypes: function(frm,cdt,cdn) {
		var child = locals[cdt][cdn];
		set_applicable_for_field_read_only(child);

		if (child.apply_to_all_doctypes === 1) {
			child.applicable_for = null;
			frm.refresh_field("permission_type_doctype");
		}	
	},
	applicable_for: function(frm,cdt,cdn) {
		var child = locals[cdt][cdn];
		if (child.apply_to_all_doctypes === 1) {
			child.applicable_for = null;
			frm.refresh_field("permission_type_doctype");
			frappe.throw(__("Uncheck the apply_to_all_document_types checkbox first"));
		}
	}
});

function toggle_hide_descendants(child) {
	let show = frappe.boot.nested_set_doctypes.includes(child.allow_doctype);
	return show
}

function set_hide_descendants_checkbox_read_only(child, hide_descendants_checkbox) {
	if (hide_descendants_checkbox) {
		cur_frm.fields_dict["permission_type_doctype"].grid.grid_rows_by_docname[child.name].set_field_property('hide_descendants','read_only',0);
	} else {
		cur_frm.fields_dict["permission_type_doctype"].grid.grid_rows_by_docname[child.name].set_field_property('hide_descendants','read_only',1);
	}
}

function set_applicable_for_field_read_only(child) {
	if (child.apply_to_all_doctypes === 1) {
		cur_frm.fields_dict["permission_type_doctype"].grid.grid_rows_by_docname[child.name].set_field_property('applicable_for','read_only',1);
	} else {
		cur_frm.fields_dict["permission_type_doctype"].grid.grid_rows_by_docname[child.name].set_field_property('applicable_for','read_only',0);
	}
}

function set_allow_doctype_filter(frm){
	var doctypes = get_selected_allow_doctypes(frm);
	console.log(doctypes)
	frm.set_query("allow_doctype", "permission_type_doctype", function (doc,cdt,cdn) {
		return {
				filters: {
					issingle: 0,
					istable: 0,
					name: ["Not In", doctypes]
				},
			}
	});
}
function get_selected_allow_doctypes(frm){
	var doctypes = []
	if (frm.doc.permission_type_doctype){
		frm.doc.permission_type_doctype.forEach(element => {
			if(element.allow_doctype){
				doctypes.push(element.allow_doctype)
			}
		});
	}
	return doctypes;
}