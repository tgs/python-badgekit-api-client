import httpretty
import unittest
import api
import jws
import json

def from_jwt(jwt, key):
    (b64_header, b64_claim, b64_sig) = jwt.split('.')
    (header, claim) = map(jws.utils.from_base64,
            (b64_header, b64_claim))
    jws.verify(header, claim, b64_sig, key, is_json=True)
    return jws.utils.decode(b64_claim)

class BKAPITest(unittest.TestCase):
    @httpretty.activate
    def test_auth_params(self):
        httpretty.register_uri(httpretty.GET, 'http://example.com/',
                body='{"app": "BadgeKit API"}')

        a = api.BadgeKitAPI('http://example.com', 's3cr3t')
        self.assert_(a.ping())

        req = httpretty.last_request()
        self.assert_('Authorization' in req.headers, 'JWT Authorization present')

        auth_hdr = req.headers['Authorization']
        self.assert_('JWT token=' in auth_hdr)
        token = auth_hdr[auth_hdr.find('"'):].strip('"')
        # Throws an exception on failure to verify
        claim = from_jwt(token, 's3cr3t')

        self.assertIn('key', claim)
        self.assertIn('exp', claim)
        self.assertEqual(claim['path'], '/')
        self.assertEqual(claim['method'], 'GET')

    @httpretty.activate
    def test_list(self):
        secret = 'asdf'
        a = api.BadgeKitAPI('http://example.com', secret)

        ret_structure = {
                u'badges': [u'real data goes here'],
                }
        httpretty.register_uri(httpretty.GET, 'http://example.com/systems/badgekit/badges',
                body=json.dumps(ret_structure))

        container = api.Container('badgekit')
        badges = a.list('badge', container)
        self.assertEqual(badges, ret_structure[u'badges'])


class ContainterTest(unittest.TestCase):
    def test_system_path(self):
        c = api.Container('mysystem', None, None)
        self.assertEqual(c._as_path(), 'systems/mysystem')

    def test_issuer_path(self):
        c = api.Container('sys', 'iss')
        self.assertEqual(c._as_path(), 'systems/sys/issuers/iss')

    def test_extra_bits(self):
        c = api.Container('sass')
        self.assertEqual(
                c._as_path('badges'),
                'systems/sass/badges')
