import httpretty
import requests
import jwt_auth
import jws
import unittest

def from_jwt(jwt, key):
    (b64_header, b64_claim, b64_sig) = jwt.split('.')
    (header, claim) = map(jws.utils.from_base64,
            (b64_header, b64_claim))
    jws.verify(header, claim, b64_sig, key, is_json=True)
    return jws.utils.decode(b64_claim)

class BKAPITest(unittest.TestCase):
    @httpretty.activate
    def test_auth(self):
        httpretty.register_uri(httpretty.GET, 'http://example.com/',
                body='{"app": "BadgeKit API"}')

        secret = 's3cr3tz'

        auth = jwt_auth.JWTAuth(secret, payload=jwt_auth.default_payload())
        resp = requests.get('http://example.com/', auth=auth)
        self.assert_(resp)

        req = httpretty.last_request()
        self.assert_('Authorization' in req.headers, 'JWT Authorization present')

        auth_hdr = req.headers['Authorization']
        self.assert_('JWT token=' in auth_hdr)
        token = auth_hdr[auth_hdr.find('"'):].strip('"')
        # Throws an exception on failure to verify
        claim = from_jwt(token, secret)
