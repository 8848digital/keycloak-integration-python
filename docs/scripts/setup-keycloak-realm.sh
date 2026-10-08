#!/usr/bin/env bash
# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
#
# Configure a Keycloak realm for one ERPNext site with Keycloak's standard
# admin CLI (kcadm.sh). Safe to run again: existing objects are kept.
#
# Usage (Keycloak in Docker):
#   KC_CONTAINER=keycloak-erpnext-keycloak-1 KEYCLOAK_ADMIN_PASSWORD=... \
#   REALM=erp SITE_URL=http://127.0.0.1:8010 CLIENT_ID=erpnext \
#   ERPNEXT_API_KEY=... ERPNEXT_API_SECRET=... \
#   docs/scripts/setup-keycloak-realm.sh
#
# Without Docker, set KCADM=/opt/keycloak/bin/kcadm.sh instead of KC_CONTAINER.
set -euo pipefail

: "${REALM:=erp}"
: "${SITE_URL:?set SITE_URL, the ERPNext site URL (same as its host_name)}"
: "${CLIENT_ID:=erpnext}"
: "${SITE_GROUP:=$(echo "$SITE_URL" | sed -E 's#^https?://##; s#[:/]+#-#g')}"
: "${KC_SERVER:=http://localhost:8080}"
: "${KEYCLOAK_ADMIN:=admin}"
: "${KEYCLOAK_ADMIN_PASSWORD:?set KEYCLOAK_ADMIN_PASSWORD}"
: "${ERPNEXT_API_KEY:?set ERPNEXT_API_KEY (API key of a System Manager in ERPNext)}"
: "${ERPNEXT_API_SECRET:?set ERPNEXT_API_SECRET}"

kcadm() {
	if [[ -n "${KC_CONTAINER:-}" ]]; then
		docker exec -i "$KC_CONTAINER" /opt/keycloak/bin/kcadm.sh "$@" --config /tmp/kcadm.config
	else
		"${KCADM:-kcadm.sh}" "$@" --config "${TMPDIR:-/tmp}/kcadm.config"
	fi
}

echo "==> Log in to $KC_SERVER as $KEYCLOAK_ADMIN"
kcadm config credentials --server "$KC_SERVER" --realm master --user "$KEYCLOAK_ADMIN" --password "$KEYCLOAK_ADMIN_PASSWORD" >/dev/null

echo "==> Realm $REALM"
kcadm get "realms/$REALM" >/dev/null 2>&1 || kcadm create realms -s realm="$REALM" -s enabled=true

echo "==> Client $CLIENT_ID (root URL $SITE_URL)"
CID=$(kcadm get clients -r "$REALM" -q clientId="$CLIENT_ID" --fields id --format csv --noquotes)
if [[ -z "$CID" ]]; then
	CID=$(kcadm create clients -r "$REALM" -i \
		-s clientId="$CLIENT_ID" -s enabled=true -s publicClient=false \
		-s standardFlowEnabled=true -s directAccessGrantsEnabled=false -s serviceAccountsEnabled=true \
		-s rootUrl="$SITE_URL" -s "redirectUris=[\"$SITE_URL/*\"]" -s "webOrigins=[\"$SITE_URL\"]" \
		-s 'attributes."post.logout.redirect.uris"="+"')
fi

echo "==> Service account roles (manage client roles, end sessions)"
kcadm add-roles -r "$REALM" --uusername "service-account-$CLIENT_ID" --cclientid realm-management \
	--rolename manage-clients --rolename view-clients --rolename manage-users

echo "==> Mapper: client roles -> userinfo claim resource_access.<client>.roles"
if ! kcadm get "clients/$CID/protocol-mappers/models" -r "$REALM" --fields name --format csv --noquotes | grep -qx "erpnext client roles"; then
	kcadm create "clients/$CID/protocol-mappers/models" -r "$REALM" \
		-s name="erpnext client roles" -s protocol=openid-connect -s protocolMapper=oidc-usermodel-client-role-mapper \
		-s 'config."usermodel.clientRoleMapping.clientId"='"$CLIENT_ID" \
		-s 'config."claim.name"=resource_access.${client_id}.roles' -s 'config."jsonType.label"=String' \
		-s 'config.multivalued=true' -s 'config."userinfo.token.claim"=true' \
		-s 'config."access.token.claim"=true' -s 'config."id.token.claim"=true'
fi

echo "==> Events: listener custom-event-listener, admin events with representation"
kcadm update events/config -r "$REALM" -s 'eventsListeners=["jboss-logging","custom-event-listener"]' \
	-s adminEventsEnabled=true -s adminEventsDetailsEnabled=true

echo "==> Site group $SITE_GROUP"
GID=$(kcadm get groups -r "$REALM" -q search="$SITE_GROUP" --fields id,name --format csv --noquotes | awk -F, -v n="$SITE_GROUP" '$2==n {print $1}')
[[ -n "$GID" ]] || GID=$(kcadm create groups -r "$REALM" -i -s name="$SITE_GROUP")
# Saving the group makes the listener encrypt client_secret.
kcadm update "groups/$GID" -r "$REALM" -s name="$SITE_GROUP" \
	-s "attributes.base_url=[\"$SITE_URL\"]" -s "attributes.client_id=[\"$ERPNEXT_API_KEY\"]" \
	-s "attributes.client_secret=[\"$ERPNEXT_API_SECRET\"]"

SECRET=$(kcadm get "clients/$CID/client-secret" -r "$REALM" --fields value --format csv --noquotes)
cat <<DONE

Done. Enter these in ERPNext > Social Login Key "Keycloak":
  Base URL      : $KC_SERVER/realms/$REALM   (use the URL browsers reach Keycloak on)
  Client ID     : $CLIENT_ID
  Client Secret : $SECRET
DONE
