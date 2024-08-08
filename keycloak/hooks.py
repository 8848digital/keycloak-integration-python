app_name = "keycloak"
app_title = "Keycloak Integration"
app_publisher = "Amandeep"
app_description = "Keycloak Integration"
app_email = "amandeep@8848digital.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/keycloak/css/keycloak.css"
# app_include_js = "/assets/keycloak/js/keycloak.js"

# include js, css files in header of web template
# web_include_css = "/assets/keycloak/css/keycloak.css"
# web_include_js = "/assets/keycloak/js/keycloak.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "keycloak/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "keycloak.utils.jinja_methods",
# 	"filters": "keycloak.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "keycloak.install.before_install"
# after_install = "keycloak.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "keycloak.uninstall.before_uninstall"
# after_uninstall = "keycloak.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "keycloak.utils.before_app_install"
# after_app_install = "keycloak.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "keycloak.utils.before_app_uninstall"
# after_app_uninstall = "keycloak.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "keycloak.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

on_logout = "keycloak.overrides.logout.logout"

doc_events = {
    "Role Profile" : {
        "before_validate": "keycloak.keycloak_integration.customizations.Role Profile.update_role_profile.update_user_roles",
        "validate": "keycloak.keycloak_integration.customizations.Role Profile.add_role_profile.add_role_profile_in_keycloak",
        "on_trash": "keycloak.keycloak_integration.customizations.Role Profile.add_role_profile.delete_role_profile_in_keycloak" 
    },
    "Module Profile" : {
        "validate": "keycloak.keycloak_integration.customizations.Module Profile.add_module_profile.add_module_profile_in_keycloak",
        "on_trash": "keycloak.keycloak_integration.customizations.Module Profile.add_module_profile.delete_module_profile_in_keycloak"
    },
    "User Permission": {
        "on_trash": "keycloak.keycloak_integration.customizations.User Permission.delete_user_permission.delete_user_permission"
    }
}
# Scheduled Tasks
# ---------------
# scheduler_events = {
# 	"all": [
# 		"keycloak.tasks.all"
# 	],
# 	"daily": [
# 		"keycloak.tasks.daily"
# 	],
# 	"hourly": [
# 		"keycloak.tasks.hourly"
# 	],
# 	"weekly": [
# 		"keycloak.tasks.weekly"
# 	],
# 	"monthly": [
# 		"keycloak.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "keycloak.install.before_tests"

# Overriding Methods
# ------------------------------
#
override_whitelisted_methods = {
	# "frappe.desk.doctype.event.event.get_events": "keycloak.event.get_events"
    "frappe.integrations.oauth2_logins.custom": "keycloak.overrides.oauth2_logins.custom"
}

# Overriding the login method to authenticate based on conditions
from frappe.auth import LoginManager
from keycloak.auth import post_login
LoginManager.post_login = post_login

#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "keycloak.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["keycloak.utils.before_request"]
# after_request = ["keycloak.utils.after_request"]

# Job Events
# ----------
# before_job = ["keycloak.utils.before_job"]
# after_job = ["keycloak.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"keycloak.auth.validate"
# ]

fixtures = [
    {"dt": "Property Setter", "filters": [
        [
            "module", "in", [
                "Keycloak Integration"
            ]
        ]
    ]},
    {"dt": "Custom Field", "filters": [
        [
            "module", "in", [
                "Keycloak Integration"
            ]
        ]
    ]}
]