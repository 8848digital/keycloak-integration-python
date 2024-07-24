import frappe
from frappe import _
from frappe.auth import validate_ip_address

# Overriding the post_login method to authenticate user based on validations
def post_login(self):
    self.run_trigger("on_login")
    validate_ip_address(self.user)
    self.validate_hour()
    self.get_user_info()
    self.make_session()
    
    doc = frappe.get_doc("User", frappe.session.user)
    if frappe.db.exists("User Permission",{"user":doc.email}) or frappe.session.user == "Administrator":
        self.setup_boot_cache()
        self.set_user_info()
    else:
        # frappe.throw("Insufficient Permissions for User")
        raise frappe.AuthenticationError()
