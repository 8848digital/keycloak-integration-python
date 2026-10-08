# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.

"""
Create the demo data of docs/erpnext-keycloak-setup.md §8 through the real
flows: Role Profiles in ERPNext (-> client roles), team groups in Keycloak,
users that join the site group and a team (-> pushed to ERPNext), and a User
and Permission Configuration per user. Safe to run again.

Usage (any Python 3.10+ with "requests"):

    ERP_URL=http://127.0.0.1:8010 ERP_API_KEY=... ERP_API_SECRET=... \
    KC_URL=http://127.0.0.1:8080 KC_ADMIN_PASSWORD=... \
    python docs/scripts/create-demo-data.py

Optional: KC_REALM (erp), KC_ADMIN_USER (admin), KC_CLIENT_ID (erpnext),
SITE_GROUP (site1), COMPANY (first company), DEMO_PASSWORD (Demo@12345).
"""

import json
import os
import time
from urllib.parse import quote

import requests

ENV = os.environ
ERP_URL = ENV.get("ERP_URL", "http://127.0.0.1:8010").rstrip("/")
KC_URL = ENV.get("KC_URL", "http://127.0.0.1:8080").rstrip("/")
REALM = ENV.get("KC_REALM", "erp")
CLIENT_ID = ENV.get("KC_CLIENT_ID", "erpnext")
SITE_GROUP = ENV.get("SITE_GROUP", "site1")
PASSWORD = ENV.get("DEMO_PASSWORD", "Demo@12345")

ROLE_PROFILES = {
	"Demo Sales Executive": ["Sales User"],
	"Demo Sales Head": ["Sales User", "Sales Manager"],
	"Demo Purchase Executive": ["Purchase User"],
	"Demo Purchase Head": ["Purchase User", "Purchase Manager"],
	"Demo Store Keeper": ["Stock User"],
	"Demo Stock Head": ["Stock User", "Stock Manager", "Item Manager"],
	"Demo Accountant": ["Accounts User"],
	"Demo Finance Head": ["Accounts User", "Accounts Manager", "Auditor"],
	"Demo HR Executive": ["HR User"],
	"Demo HR Head": ["HR User", "HR Manager"],
	"Demo Project Lead": ["Projects User", "Projects Manager"],
	"Demo Support Analyst": ["Support Team", "Report Manager", "Analytics"],
}
TEAMS = {
	"Sales Team": ["Demo Sales Executive"],
	"Stores Team": ["Demo Store Keeper"],
	"Finance Team": ["Demo Accountant"],
	"Managers": ["Demo Sales Head", "Demo Finance Head"],
}
USERS = {
	"team.sales1": "Sales Team", "team.sales2": "Sales Team", "team.sales3": "Sales Team",
	"team.store1": "Stores Team", "team.store2": "Stores Team",
	"team.fin1": "Finance Team", "team.fin2": "Finance Team",
	"team.manager1": "Managers",
}
PERMISSION_TYPE = "PT Company"


def main():
	"""
	Create every demo object, then print what ERPNext shows for each user.

	Returns:
		None
	"""
	erp = erp_session()
	kc = keycloak_session()
	company = ENV.get("COMPANY") or erp.get(f"{ERP_URL}/api/resource/Company").json()["data"][0]["name"]

	create_role_profiles(erp)
	client_uuid = kc_get(kc, "clients", params={"clientId": CLIENT_ID})[0]["id"]
	team_ids = create_teams(kc, client_uuid)
	site_id = find_group(kc, SITE_GROUP)["id"]
	create_permission_type(erp)

	for username, team in USERS.items():
		email = f"{username}@example.com"
		user_id = create_keycloak_user(kc, username, email)
		kc.put(f"{admin_url()}/users/{user_id}/groups/{site_id}").raise_for_status()
		kc.put(f"{admin_url()}/users/{user_id}/groups/{team_ids[team]}").raise_for_status()
		wait_for(lambda email=email: erp.get(f"{ERP_URL}/api/resource/User/{quote(email)}").ok)
		give_access(erp, email, company)

	report(erp)


def create_role_profiles(erp):
	"""Create the demo Role Profiles; ERPNext creates the client roles."""
	for name, roles in ROLE_PROFILES.items():
		if not erp.get(f"{ERP_URL}/api/resource/Role Profile/{quote(name)}").ok:
			response = erp.post(f"{ERP_URL}/api/resource/Role Profile",
				json={"role_profile": name, "roles": [{"role": role} for role in roles]})
			response.raise_for_status()


def create_teams(kc, client_uuid):
	"""Create team groups and grant their client roles. Returns {team: group id}."""
	team_ids = {}
	for team, role_names in TEAMS.items():
		group = find_group(kc, team)
		if not group:
			kc.post(f"{admin_url()}/groups", json={"name": team}).raise_for_status()
			group = find_group(kc, team)
		roles = [kc_get(kc, f"clients/{client_uuid}/roles/{quote(name)}") for name in role_names]
		kc.post(f"{admin_url()}/groups/{group['id']}/role-mappings/clients/{client_uuid}",
			json=[{"id": role["id"], "name": role["name"]} for role in roles]).raise_for_status()
		team_ids[team] = group["id"]
	return team_ids


def create_permission_type(erp):
	"""Create "PT Company" (Company, apply to all DocTypes) when missing."""
	if not erp.get(f"{ERP_URL}/api/resource/Permission Type/{quote(PERMISSION_TYPE)}").ok:
		erp.post(f"{ERP_URL}/api/resource/Permission Type", json={"name1": PERMISSION_TYPE,
			"permission_type_doctype": [{"allow_doctype": "Company", "apply_to_all_doctypes": 1}]}).raise_for_status()


def create_keycloak_user(kc, username, email):
	"""Create the Keycloak user with a password when missing. Returns the user id."""
	found = kc_get(kc, "users", params={"username": username, "exact": "true"})
	if not found:
		first, last = username.split(".", 1)
		kc.post(f"{admin_url()}/users", json={"username": username, "email": email,
			"firstName": first.title(), "lastName": last.title(), "enabled": True, "emailVerified": True,
			"credentials": [{"type": "password", "value": PASSWORD, "temporary": False}]}).raise_for_status()
		found = kc_get(kc, "users", params={"username": username, "exact": "true"})
	return found[0]["id"]


def give_access(erp, email, company):
	"""Create the user's User and Permission Configuration when missing."""
	name = f"{email}-{PERMISSION_TYPE}"
	if not erp.get(f"{ERP_URL}/api/resource/User and Permission Configuration/{quote(name)}").ok:
		erp.post(f"{ERP_URL}/api/resource/User and Permission Configuration", json={"user": email,
			"permission_type": PERMISSION_TYPE,
			"user_permission_doctype_value": [{"doc_type": "Company", "for_value": company}]}).raise_for_status()


def report(erp):
	"""Print each demo user's ERPNext roles."""
	for username, team in USERS.items():
		user = erp.get(f"{ERP_URL}/api/resource/User/{quote(username + '@example.com')}").json()["data"]
		roles = sorted(row["role"] for row in user["roles"])
		print(f"{username:15} {team:13} enabled={user['enabled']} roles={', '.join(roles)}")


def erp_session():
	"""ERPNext session authenticated with API key and secret."""
	session = requests.Session()
	session.headers["Authorization"] = f"token {ENV['ERP_API_KEY']}:{ENV['ERP_API_SECRET']}"
	return session


def keycloak_session():
	"""Keycloak admin session (master realm, admin-cli)."""
	response = requests.post(f"{KC_URL}/realms/master/protocol/openid-connect/token", data={
		"grant_type": "password", "client_id": "admin-cli",
		"username": ENV.get("KC_ADMIN_USER", "admin"), "password": ENV["KC_ADMIN_PASSWORD"]}, timeout=20)
	response.raise_for_status()
	session = requests.Session()
	session.headers["Authorization"] = f"Bearer {response.json()['access_token']}"
	return session


def admin_url():
	"""Admin REST base URL of the realm."""
	return f"{KC_URL}/admin/realms/{REALM}"


def kc_get(kc, path, **kwargs):
	"""GET one Admin REST resource and return its JSON."""
	response = kc.get(f"{admin_url()}/{path}", timeout=30, **kwargs)
	response.raise_for_status()
	return response.json()


def find_group(kc, name):
	"""Return the top-level group with this exact name, or None."""
	return next((group for group in kc_get(kc, "groups", params={"search": name}) if group["name"] == name), None)


def wait_for(check, seconds=10):
	"""Poll until check() is true (the listener pushes asynchronously after commit)."""
	end = time.time() + seconds
	while time.time() < end and not check():
		time.sleep(0.3)


if __name__ == "__main__":
	main()
	print(json.dumps({"done": True}))
