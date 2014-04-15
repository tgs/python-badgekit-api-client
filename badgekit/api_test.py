import httpretty
import unittest
import api
import jws

def from_jwt(jwt, key):
    (b64_header, b64_claim, b64_sig) = jwt.split('.')
    (header, claim) = map(jws.utils.from_base64,
            (b64_header, b64_claim))
    jws.verify(header, claim, b64_sig, key, is_json=True)
    return jws.utils.decode(b64_claim)

class BKAPITest(unittest.TestCase):
    @httpretty.activate
    def test_ping(self):
        httpretty.register_uri(httpretty.GET, 'http://example.com/',
                body='')

        a = api.BadgeKitAPI('http://example.com', 's3cr3t')
        a.ping()

        self.assertEqual(httpretty.last_request().path, '/')

    @httpretty.activate
    def test_auth(self):
        httpretty.register_uri(httpretty.GET, 'http://example.com/',
                body='')

        a = api.BadgeKitAPI('http://example.com', 's3cr3t')
        self.assert_(a.ping())

        req = httpretty.last_request()
        self.assert_('Authorization' in req.headers, 'JWT Authorization present')

        auth_hdr = req.headers['Authorization']
        self.assert_('JWT token=' in auth_hdr)
        token = auth_hdr[auth_hdr.find('"'):].strip('"')
        # Throws an exception on failure to verify
        claim = from_jwt(token, 's3cr3t')
