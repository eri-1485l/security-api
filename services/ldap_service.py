import os
import ldap

class LDAPService:
    def __init__(self):
        self.server = os.getenv("LDAP_SERVER", "ldap://localhost:389")
        self.base_dn = os.getenv("LDAP_BASE_DN", "dc=example,dc=com")
        self.admin_dn = os.getenv("LDAP_ADMIN_DN", "cn=admin,dc=example,dc=com")
        self.admin_password = os.getenv("LDAP_ADMIN_PASSWORD", "adminpassword")

    def authenticate(self, username: str, password: str) -> bool:
        user_dn = f"uid={username},ou=users,{self.base_dn}"
        try:
            conn = ldap.initialize(self.server)
            conn.set_option(ldap.OPT_REFERRALS, 0)
            conn.simple_bind_s(user_dn, password)
            conn.unbind_s()
            return True
        except ldap.INVALID_CREDENTIALS:
            return False
        except ldap.LDAPError as e:
            print(f"LDAP error: {e}")
            return False

    def get_user_dn(self, username: str) -> str:
        return f"uid={username},ou=users,{self.base_dn}"