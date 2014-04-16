import requests
import posixpath
import jwt_auth
from urlparse import urljoin
import json
import collections

# Exceptions corresponding to errors the API can return
class MethodNotAllowedError(ValueError): pass
class ResourceNotFound(ValueError): pass

errors = {
        'MethodNotAllowedError': MethodNotAllowedError,
        'ResourceNotFound': ResourceNotFound,
        }

def raise_error(resp_obj):
    try:
        exc_type = errors[resp_obj['code']]
        resp_obj['message']
    except:
        raise TypeError(str(resp_obj))

    raise exc_type(resp_obj['message'])


# Code to construct paths in the BadgeKit API
_path_order = (
        'system',
        'issuer',
        'program',
        'badge',
        'instance',
        'application',
        'evidence',
        'comment',
        'code',
        )


def _api_plural(noun):
    if noun != 'evidence':
        return noun + 's'
    else:
        return 'evidence'


def _make_path(*args, **kwargs):
    '''
    Constructs URL paths such as 'systems/{system}/issuers/{issuer}.
    '''
    parts = []
    for field in _path_order:
        value = kwargs.get(field)
        if not value:
            continue
        parts.extend([_api_plural(field), value])

    if args:
        parts.extend(args)

    return posixpath.join(*parts)


class BadgeKitAPI(object):
    def __init__(self, baseurl, secret, key='master'):
        self.baseurl = baseurl

        jwt_payload = jwt_auth.default_payload()
        jwt_payload['key'] = key
        jwt_payload['exp'] = jwt_auth.exp_after(30)
        self.auth = jwt_auth.JWTAuth(secret, payload=jwt_payload)

    def ping(self):
        "Tests the server's availability"
        resp = requests.get(urljoin(self.baseurl, '/'), auth=self.auth)
        resp_dict = json.loads(resp.text)
        return resp.status_code == 200 and resp_dict['app'] == 'BadgeKit API'

    def list(self, kind, **kwargs):
        "Lists objects of some kind in a container"
        kind_plural = _api_plural(kind)
        path = _make_path(kind_plural, **kwargs)
        resp = requests.get(urljoin(self.baseurl, path), auth=self.auth)
        resp_obj = json.loads(resp.text)
        if resp.status_code != 200:
            raise_error(resp_obj)
        return resp_obj[kind_plural]
