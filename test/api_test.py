from __future__ import unicode_literals
import httpretty
import requests
import re
import unittest
import badgekit
from badgekit import api
import jwt
import json


class BKAPITest(unittest.TestCase):
    @httpretty.activate
    def test_auth_params(self):
        httpretty.register_uri(httpretty.GET, 'http://example.com/',
                body='{"app": "BadgeKit API"}')

        a = badgekit.BadgeKitAPI('http://example.com', 's3cr3t')
        self.assertTrue(a.ping())

        req = httpretty.last_request()
        self.assertTrue('Authorization' in req.headers, 'JWT Authorization present')

        auth_hdr = req.headers['Authorization']
        self.assertTrue('JWT token=' in auth_hdr)
        token = auth_hdr[auth_hdr.find('"'):].strip('"')
        # Throws an exception on failure to verify
        claim = jwt.decode(token, 's3cr3t')

        self.assertTrue('key' in claim)
        self.assertTrue('exp' in claim)
        self.assertEqual(claim['path'], '/')
        self.assertEqual(claim['method'], 'GET')

    @httpretty.activate
    def test_list(self):
        a = badgekit.BadgeKitAPI('http://example.com', 'asdf')

        ret_structure = {
                'badges': ['real data goes here'],
                }
        httpretty.register_uri(httpretty.GET,
                re.compile('example.com/.*'),
                body=json.dumps(ret_structure))

        badges = a.list('badge', system='badgekit')
        self.assertEqual(badges, ret_structure)

        req = httpretty.last_request()
        self.assertEqual(req.path, '/systems/badgekit/badges')

    @httpretty.activate
    def test_get(self):
        a = badgekit.BadgeKitAPI('http://example.com/', 'asdf')

        slug = 'the-machine'
        ret_structure = { 'system':
                { 'email': None, 'id': 1, 'imageUrl': None, 'slug': slug },
                }
        httpretty.register_uri(httpretty.GET,
                re.compile('example.com/.*'),
                body=json.dumps(ret_structure))

        resp = a.get(system=slug)
        self.assertEqual(resp['system'], ret_structure['system'])

        req = httpretty.last_request()
        self.assertEqual(req.path, '/systems/the-machine')

    @httpretty.activate
    def test_create(self):
        a = badgekit.BadgeKitAPI('http://example.com/', 'asdf')

        slug = 'test-sys'
        httpretty.register_uri(httpretty.POST,
                re.compile('example.com/.*'),
                body='{}', status=201)

        result = a.create(
                'system',
                dict(slug=slug, name='Test System FTW',
                    url='http://example.com/testz'))

        req = httpretty.last_request()
        self.assertEqual(req.path, '/systems')


class PathTest(unittest.TestCase):
    def test_system_path(self):
        c = dict(system='mysystem')
        self.assertEqual(api._make_path(**c), 'systems/mysystem')

    def test_issuer_path(self):
        c = dict(system='sys', issuer='iss')
        self.assertEqual(api._make_path(**c), 'systems/sys/issuers/iss')

    def test_extra_bits(self):
        c = dict(system='sass')
        self.assertEqual(
                api._make_path('badges', **c),
                'systems/sass/badges')

    def test_query(self):
        self.assertEqual(
                api._make_path('badges', system='jkl', archived=True),
                'systems/jkl/badges?archived=true')


class ServerVersionTest(unittest.TestCase):
    @httpretty.activate
    def test_find_version(self):
        a = badgekit.BadgeKitAPI('http://example.com', 'asdf')

        httpretty.register_uri(httpretty.GET,
                re.compile('example.com/.*'),
                body='{"app":"BadgeKit API","version":"0.2.9"}')

        resp = a.server_version()
        self.assertEqual(resp, "0.2.9")


    @httpretty.activate
    def test_require_version(self):
        a = badgekit.BadgeKitAPI('http://example.com', 'asdf')

        httpretty.register_uri(httpretty.GET,
                re.compile('example.com/.*'),
                body='{"app":"BadgeKit API","version":"0.2.9"}')

        try:
            a.require_server_version("0.3.0")
            self.fail("Should have thrown exception")
        except ValueError:
            pass

        a.require_server_version("0.2")
        a.require_server_version("0.2.2")


class ExceptionTest(unittest.TestCase):
    def test_known_str(self):
        req = requests.Request("POST", "http://example.org/system/")
        response = {
                "code": "ResourceConflict",
                "message": "system with that `slug` already exists",
                "details": {
                    "slug": "system-slug",
                    "name": "System Name",
                    "url": "https://example.org/system/",
                    "email": "system-badges@example.org",
                    "description": "System Description"
                    }
                }
        e = badgekit.ResourceConflict(response, req)
        self.assertTrue('ResourceConflict' in str(e))
        self.assertTrue('already exists' in str(e))

    def test_unknown_code(self):
        req = requests.Request("POST", "http://example.org/systems/")
        response = {
                "there's no code field": "yup",
                }

        try:
            api.raise_error(response, req)
            self.fail("Exception should have been raised")
        except badgekit.BadgeKitException as e:
            self.assertTrue('example.org/systems' in '%s' % e)

    @httpretty.activate
    def test_invalid_json(self):
        a = badgekit.BadgeKitAPI('http://example.com', 'asdf')

        httpretty.register_uri(httpretty.GET,
                re.compile('example.com/.*'),
                body='{invalid json')

        try:
            badges = a.list('badge', system='badgekit')
            self.fail("Exception should have been raised")
        except badgekit.APIError as e:
            self.assertTrue('json' in ('%s' % e).lower())
