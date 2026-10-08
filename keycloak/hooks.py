# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.

app_name = "keycloak"
app_title = "Keycloak Integration"
app_publisher = "8848 Digital LLP"
app_description = "Keycloak Integration"
app_email = "amandeep@8848digital.com"
app_license = "Proprietary"

required_apps = ["frappe"]

# Fixtures
# --------
# Exported with `bench --site <site> 8848-export-fixtures`.

custom_fixtures = [
	{"dt": "Custom Field", "filters": {"module": ["in", ["Keycloak Integration"]]}},
]

commands = ["keycloak.commands.export_fixtures.export_fixtures"]

# Authentication
# --------------

# Order matters: apply Keycloak roles first, then the User Permission check.
on_login = [
	"keycloak.keycloak_integration.login.sync_roles_from_keycloak",
	"keycloak.keycloak_integration.login.validate_user_permission",
]
on_logout = "keycloak.keycloak_integration.sso_session.logout"

# Document Events
# ---------------

doc_events = {
	"Role Profile": {
		"before_validate": "keycloak.keycloak_integration.customization.role_profile.role_profile.before_validate",
		"validate": "keycloak.keycloak_integration.customization.role_profile.role_profile.validate",
		"on_trash": "keycloak.keycloak_integration.customization.role_profile.role_profile.on_trash",
	},
	"User Permission": {
		"on_trash": "keycloak.keycloak_integration.customization.user_permission.user_permission.on_trash",
	},
	"Social Login Key": {
		"before_validate": "keycloak.keycloak_integration.customization.social_login_key.social_login_key.before_validate",
	},
}

# Overriding Methods
# ------------------

override_whitelisted_methods = {
	"frappe.integrations.oauth2_logins.login_via_keycloak": "keycloak.keycloak_integration.api.v1.oauth.login_via_keycloak",
	# Legacy path of the access_token endpoint.
	"keycloak.sdk.api": "keycloak.keycloak_integration.api.v1.sdk.api",
}
