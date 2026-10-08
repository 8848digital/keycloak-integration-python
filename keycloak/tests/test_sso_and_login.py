# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.

"""Tests for the login guard, SSO logout and the Keycloak Admin API helpers."""

from types import SimpleNamespace
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from keycloak.keycloak_integration import sso_session
from keycloak.keycloak_integration.login import validate_user_permission
from keycloak.tests.utils import FakeResponse, make_keycloak_login_key, make_user
from keycloak.utils import keycloak_admin


class TestLoginGuard(FrappeTestCase):
	"""on_login rejects users without a User Permission."""

	def test_user_without_permission_is_rejected(self):
		"""No User Permission -> AuthenticationError before a session exists."""
		make_user("kc-no-permission@example.com")
		with self.assertRaises(frappe.AuthenticationError):
			validate_user_permission(SimpleNamespace(user="kc-no-permission@example.com"))

	def test_user_with_permission_is_allowed(self):
		"""A User Permission lets the login continue."""
		make_user("kc-with-permission@example.com")
		frappe.get_doc(
			{
				"doctype": "User Permission",
				"user": "kc-with-permission@example.com",
				"allow": "Company",
				"for_value": frappe.get_all("Company", pluck="name", limit=1)[0],
			}
		).insert(ignore_permissions=True)
		validate_user_permission(SimpleNamespace(user="kc-with-permission@example.com"))

	def test_administrator_is_allowed(self):
		"""Administrator never needs a User Permission."""
		validate_user_permission(SimpleNamespace(user="Administrator"))

	def test_hook_is_wired_without_monkeypatch(self):
		"""The guard is an on_login hook; LoginManager.post_login is untouched."""
		from frappe.auth import LoginManager

		self.assertEqual(
			frappe.get_hooks("on_login")[-2:],
			[
				"keycloak.keycloak_integration.login.sync_roles_from_keycloak",
				"keycloak.keycloak_integration.login.validate_user_permission",
			],
		)
		self.assertEqual(LoginManager.post_login.__module__, "frappe.auth")


class TestSsoLogout(FrappeTestCase):
	"""Logout deletes only the server-side remembered Keycloak session."""

	def setUp(self):
		"""
		Give the test a fake logged-in session id.

		Returns:
			None
		"""
		self.original_sid = frappe.session.sid
		frappe.session.sid = "kc-test-sid"

	def tearDown(self):
		"""
		Restore the real session id.

		Returns:
			None
		"""
		frappe.session.sid = self.original_sid

	def test_logout_deletes_remembered_session(self):
		"""The stored session_state is sent to Keycloak, URL-encoded, once."""
		sso_session.remember_sso_session("keycloak", "state/../1")
		with (
			patch.object(sso_session, "get_keycloak_access_token", return_value="token"),
			patch.object(sso_session, "admin_request", return_value=FakeResponse(204)) as admin_request,
		):
			sso_session.logout()
			sso_session.logout()

		admin_request.assert_called_once_with("DELETE", "sessions/state%2F..%2F1", "token")

	def test_logout_without_sso_session_does_nothing(self):
		"""Password logins have no stored state, so Keycloak is not called."""
		with patch.object(sso_session, "admin_request") as admin_request:
			sso_session.logout()

		admin_request.assert_not_called()

	def test_logout_failure_never_raises(self):
		"""A Keycloak outage must not block the ERPNext logout."""
		sso_session.remember_sso_session("keycloak", "state-2")
		with patch.object(sso_session, "get_keycloak_access_token", side_effect=Exception("down")):
			sso_session.logout()


class TestKeycloakAdmin(FrappeTestCase):
	"""URL building and the client-credentials token request."""

	def test_join_url(self):
		"""Slashes are normalised between parts."""
		self.assertEqual(keycloak_admin.join_url("http://kc/", "/realms/", "erp"), "http://kc/realms/erp")

	def test_admin_realm_url_and_token(self):
		"""The token request uses the derived base_url and a timeout."""
		make_keycloak_login_key()
		self.assertEqual(keycloak_admin.get_admin_realm_url(), "http://keycloak.test/admin/realms/erp")

		with patch.object(
			keycloak_admin.requests, "post", return_value=FakeResponse(200, {"access_token": "abc"})
		) as post:
			self.assertEqual(keycloak_admin.get_keycloak_access_token(), "abc")

		url = post.call_args.args[0]
		self.assertEqual(url, "http://keycloak.test/realms/erp/protocol/openid-connect/token")
		self.assertEqual(post.call_args.kwargs["timeout"], keycloak_admin.REQUEST_TIMEOUT)
		self.assertEqual(post.call_args.kwargs["data"]["client_secret"], "erp-secret")

	def test_disabled_keycloak_returns_no_token(self):
		"""With enable_keycloak off, nothing is sent to Keycloak."""
		make_keycloak_login_key(enabled=0)
		with patch.object(keycloak_admin.requests, "post") as post:
			self.assertIsNone(keycloak_admin.get_keycloak_access_token())

		post.assert_not_called()

	def tearDown(self):
		"""
		Remove the test Social Login Key.

		Returns:
			None
		"""
		frappe.delete_doc("Social Login Key", "keycloak", ignore_missing=True, force=True)


class TestKeycloakCallback(FrappeTestCase):
	"""The callback is Frappe's standard flow plus the userinfo / session_state hand-off."""

	def test_callback_runs_standard_flow(self):
		"""Standard get_info_via_oauth + login_oauth_user, with userinfo kept for on_login."""
		from keycloak.keycloak_integration.api.v1 import oauth

		self.assertEqual(
			frappe.override_whitelisted_method("frappe.integrations.oauth2_logins.login_via_keycloak"),
			"keycloak.keycloak_integration.api.v1.oauth.login_via_keycloak",
		)
		userinfo = {"email": "kc-cb@example.com"}
		with (
			patch.object(oauth, "get_info_via_oauth", return_value=userinfo) as get_info,
			patch.object(oauth, "login_oauth_user") as login_user,
			patch.object(oauth, "remember_sso_session") as remember,
		):
			oauth.login_via_keycloak(code="c", state="s", session_state="ss", iss="x")

		self.assertEqual(get_info.call_args.args[:2], ("keycloak", "c"))
		login_user.assert_called_once_with(userinfo, provider="keycloak", state="s")
		remember.assert_called_once_with("keycloak", "ss")
		self.assertIs(frappe.flags.keycloak_userinfo, userinfo)
		frappe.flags.keycloak_userinfo = None

	def test_refused_login_keeps_new_user_and_shows_page(self):
		"""A user without a User Permission gets a 403 page, and the new user is kept."""
		from keycloak.keycloak_integration.api.v1 import oauth

		with (
			patch.object(oauth, "get_info_via_oauth", return_value={"email": "kc-new@example.com"}),
			patch.object(oauth, "login_oauth_user", side_effect=frappe.AuthenticationError),
			patch.object(frappe.db, "commit") as commit,
			patch.object(oauth, "delete_keycloak_session") as delete_session,
			patch.object(frappe, "respond_as_web_page") as respond,
		):
			oauth.login_via_keycloak(code="c", state="s", session_state="ss")

		commit.assert_called_once()
		delete_session.assert_called_once_with("ss", notify=False)
		self.assertEqual(respond.call_args.kwargs["http_status_code"], 403)
		frappe.flags.keycloak_userinfo = None
