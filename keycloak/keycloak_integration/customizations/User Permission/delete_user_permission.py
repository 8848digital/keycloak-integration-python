import frappe
from frappe import _

def delete_user_permission(doc, method):
    print("1")
    # if frappe.db.exists("User Permission Doctype Value",{"user_permission_record": doc.name}):
    #     query = frappe.db.sql(f"""
    #                 SELECT 
    #                 uapc.name
    #                 FROM `tabUser and Permission Configuration` as uapc
    #                 LEFT JOIN `tabUser Permission Doctype Value` as updv
    #                 ON updv.parent = uapc.name
    #                 WHERE updv.user_permission_record = '{doc.name}'
    #             """,as_dict=True)
    #     if query:
    #         print("query : ", query[0].get("name"))
    #         doctype = "User and Permission Configuration"
    #         docname = query[0].get("name")
    #         link = frappe.utils.get_url_to_form(doctype, docname)
    #         print("link : ", link)
            
    #         message = _(
    #             f"Cannot delete the record as it is linked with <a href='{link}'>{docname}</a>"
    #         )

    #         frappe.throw(_(message))