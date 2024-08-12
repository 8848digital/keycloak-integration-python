def before_validate(doc, method = None):
    set_missing_url(doc)


def set_missing_url(doc, method = None):
    if doc.name == "keycloak":
        if not doc.base_url and doc.root_url and doc.realm_name: 
            if "/" == doc.root_url[-1]:
                doc.base_url = doc.root_url +"realms/"+ doc.realm_name
            else:
                doc.base_url = doc.root_url +"/realms/"+ doc.realm_name
        if doc.base_url and not doc.root_url and not doc.realm_name and "realms" in doc.base_url:
            base_url = doc.base_url.split("realms")
            doc.root_url = base_url[0]
            doc.realm_name = base_url[1].split("/")[1]
