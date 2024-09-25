import frappe
import requests
import json
import urllib.parse
from keycloak.utils.utils import get_access_token
from urllib.parse import urljoin

def logout():
    provider = frappe.request.cookies.get('provider')
    if provider == "keycloak":
        logout_user_from_provider(provider)

def logout_user_from_provider(provider):
    base_url = frappe.get_value("Social Login Key", provider, "base_url")
    encoded_string = frappe.request.cookies.get(provider)
    decoded_string = urllib.parse.unquote(encoded_string.strip('%22'))
    params = urllib.parse.parse_qs(decoded_string)
    session_state = params.get('session_state', [None])[0]
    if base_url and session_state:
        delete_keycloak_session(base_url, session_state, provider)

def delete_keycloak_session(base_url, session_state, provider):
    base_url = base_url.replace("realms", "admin/realms")
    url = f"{base_url}sessions/{session_state}"
    access_token = get_access_token()
    if not base_url.endswith('/'):
        base_url += '/'
    url = urljoin(base_url, f"sessions/{session_state}")
    headers = {
    'Authorization': f'Bearer {access_token}'
    }
    response = requests.delete(url, headers=headers)
    if response.status_code == 204:
        error_log = {
        "response": response.text,
        "base_url": base_url,
        "session_state": session_state,
        "access_token": access_token
        }
        frappe.msgprint(f"Logout successfully from {frappe.get_value('Social Login Key', provider, 'provider_name')}")
    else:
        frappe.log_error("SSO Logout Error", error_log)
        frappe.msgprint(f"Logout from {frappe.get_value('Social Login Key', provider, 'provider_name')} failed")

def send_logout_request(base_url, logout_endpoint, client_id, client_secret, refresh_token, provider):
    url = f"{base_url}{logout_endpoint}"
    payload = {
            'client_id': client_id,
            'client_secret': client_secret,
            'refresh_token': refresh_token
        }
    headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
    response = requests.post(url, data=payload, headers=headers)
    if response.status_code == 204:
        frappe.msgprint(f"Logout successfully from {frappe.get_value('Social Login Key', provider, 'provider_name')}")
    else:
        frappe.msgprint(f"Logout from {frappe.get_value('Social Login Key', provider, 'provider_name')} failed")

