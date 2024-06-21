
import frappe
import json
from frappe.utils.oauth import Callable, get_oauth2_flow, get_oauth2_providers, get_redirect_uri


def get_info_via_oauth(provider: str, code: str, decoder: Callable | None = None, id_token: bool = False):
	import jwt

	flow = get_oauth2_flow(provider)
	oauth2_providers = get_oauth2_providers()

	args = {
		"data": {
			"code": code,
			"redirect_uri": get_redirect_uri(provider),
			"grant_type": "authorization_code",
		}
	}

	if decoder:
		args["decoder"] = decoder

	session = flow.get_auth_session(**args)
	parsed_access = json.loads(session.access_token_response.text)
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

		if provider == "github" and not info.get("email"):
			emails = session.get("/user/emails", params=api_endpoint_args).json()
			email_dict = next(filter(lambda x: x.get("primary"), emails))
			info["email"] = email_dict.get("email")

	if not (info.get("email_verified") or info.get("email")):
		frappe.throw(_("Email not verified with {0}").format(provider.title()))

	return info