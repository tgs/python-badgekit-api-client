import requests
import jwt_auth
from urlparse import urljoin

class BadgeKitAPI(object):
    def __init__(self, baseurl, secret, key='master'):
        self.baseurl = baseurl

        jwt_payload = jwt_auth.default_payload()
        jwt_payload['key'] = key
        jwt_payload['exp'] = jwt_auth.exp_after(30)
        self.auth = jwt_auth.JWTAuth(secret, payload=jwt_payload)

    def ping(self):
        return requests.get(urljoin(self.baseurl, '/'), auth=self.auth)


    def list(self, kind, context):
        pass
