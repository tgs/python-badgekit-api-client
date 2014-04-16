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

class Container(collections.namedtuple('Container', 'system, issuer, program, badge')):
    """
    Represents a path to something in the API that can contain other things.

    This actually includes badges, not just 'containers' - a rename should happen.  TODO
    """
    def __new__(typ, *args):
        # Fill in unspecified fields with None
        args += (None,) * (len(typ._fields) - len(args))
        return super(Container, typ).__new__(typ, *args)

    def _as_path(self, *extras):
        '''
        Constructs URL paths such as 'systems/{system}/issuers/{issuer}.
        '''
        if not self.system:
            raise ValueError('Container requires at least a System')
        parts = []
        for field in self._fields:
            value = getattr(self, field)
            if not value:
                continue
            parts.extend([field + 's', value])

        return posixpath.join(*(parts + list(extras)))


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

    def list(self, kind, container):
        "Lists objects of some kind in a container"
        kind_plural = kind + u's'
        path = container._as_path(kind_plural)
        resp = requests.get(urljoin(self.baseurl, path), auth=self.auth)
        resp_obj = json.loads(resp.text)
        if resp.status_code != 200:
            raise_error(resp_obj)
        return resp_obj[kind_plural]
