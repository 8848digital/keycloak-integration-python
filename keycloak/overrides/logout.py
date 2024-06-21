import frappe
import requests
import json
import urllib.parse

def logout():
    provider = frappe.request.cookies.get('provider')
    if provider:
        logout_user_from_provider(provider)

def logout_user_from_provider(provider):
    provider_details = frappe.get_doc("Social Login Key", provider)
    if provider_details.logout_url:
        client_secret = provider_details.get_password("client_secret")
        access_token_details = json.loads(urllib.parse.unquote(frappe.request.cookies.get(provider)))
        if (provider_details.base_url
            and provider_details.logout_url
            and provider_details.client_id 
            and client_secret
            and access_token_details.get("refresh_token")
            and provider
            ):
            send_logout_request(provider_details.base_url, 
                                provider_details.logout_url, 
                                provider_details.client_id, 
                                client_secret, 
                                access_token_details.get("refresh_token"), 
                                provider)

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

