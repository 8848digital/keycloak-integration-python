
import frappe
import json
from frappe.utils.oauth import Callable, get_oauth2_flow, get_oauth2_providers, get_redirect_uri, login_oauth_user


# def login_via_oauth2(provider: str, code: str, state: str, decoder: Callable | None = None):
# 	info = get_info_via_oauth(provider, code, decoder)
# 	login_oauth_user(info, provider=provider, state=state)


def get_info_via_oauth(provider: str, code: str, decoder: Callable | None = None, id_token: bool = False):
	try:
		import jwt
		frappe.log_error("SSO 1")

		flow = get_oauth2_flow(provider)
		frappe.log_error("SSO 2")
		oauth2_providers = get_oauth2_providers()
		frappe.log_error("SSO 3")

		args = {
			"data": {
				"code": code,
				"redirect_uri": get_redirect_uri(provider),
				"grant_type": "authorization_code",
			}
		}
		frappe.log_error("SSO 4")
		if decoder:
			args["decoder"] = decoder

		session = flow.get_auth_session(**args)
		frappe.log_error("SSO 5")
		parsed_access = json.loads(session.access_token_response.text)
		frappe.log_error("SSO 6")
		frappe.local.cookie_manager.set_cookie("provider", provider)
		frappe.local.cookie_manager.set_cookie(provider, json.dumps(parsed_access))

		if id_token:
			parsed_access = json.loads(session.access_token_response.text)
			token = parsed_access["id_token"]
			info = jwt.decode(token, flow.client_secret, options={"verify_signature": False})

		else:
			api_endpoint = oauth2_providers[provider].get("api_endpoint")
			api_endpoint_args = oauth2_providers[provider].get("api_endpoint_args")
			info = session.get(api_endpoint, params=api_endpoint_args).json()
			frappe.log_error("SSO 7")

			if provider == "github" and not info.get("email"):
				emails = session.get("/user/emails", params=api_endpoint_args).json()
				email_dict = next(filter(lambda x: x.get("primary"), emails))
				info["email"] = email_dict.get("email")
			frappe.log_error("SSO 8")

		if not (info.get("email_verified") or info.get("email")):
			frappe.throw(_("Email not verified with {0}").format(provider.title()))

		return info
	except Exception as e:
		frappe.log_error("SSO", frappe.get_traceback(with_context=True))