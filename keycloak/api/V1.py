import frappe
from keycloak.utils import success_response, error_response
import keycloak.api.v1.access_token as access_token
import keycloak.api.v1.map_users as map_users
import keycloak.api.v1.map_roles as map_roles
import keycloak.api.v1.keycloak_erp_group_map as keycloak_erp_group_map
# import keycloak.api.v1.map_groups as map_groups
import keycloak.api.v1.assign_role_profile as assign_role_profile

class V1():
    def __init__(self):
        self.methods = {
            'access_token':['get_access_token'],
            'map_users':['map_users_in_frappe'],
            'map_roles':['map_roles_in_frappe'],
            'unassign_roles':['unassign_role_of_a_user'],
            'keycloak_erp_group_map':['map_groups_in_frappe'],
            # 'map_groups':['map_user_type_in_frappe'],
            'assign_role_profile': ["assign_role_profile_in_frappe"]
            }
    def class_map(self, kwargs):
        # print("entity")
        entity = kwargs.get('entity')
        method = kwargs.get('method')
        if self.methods.get(entity):
            if method in self.methods.get(entity):
                function = f"{kwargs.get('entity')}.{kwargs.get('method')}({kwargs})"
                return eval(function)
            else:
                return error_response("Method Not Found!")
        else:
            return error_response("Entity Not Found!")
