import requests
import urllib
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


# Possible query parameters.  As long as the list of possible
# parameters is disjoint from the set of directory components
# above, everything is easy :)
_possible_query_params = (
        'archived',
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
        if value is None:
            continue
        parts.extend([_api_plural(field), value])

    if args:
        parts.extend(args)

    path = posixpath.join(*parts)

    # If the API ever supports duplicate parameters, we would need
    # to change this to a defaultdict(list) or FieldStorage or similar.
    params = {}
    for param in _possible_query_params:
        value = kwargs.get(param)
        if value is None:
            continue
        elif value is True:
            value = 'true'
        elif value is False:
            value = 'false'
        params[param] = value

    if params:
        path = '%s?%s' % (path,
                urllib.urlencode(params))
    return path


class BadgeKitAPI(object):
    """
    A low-level interface to the BadgeKit API.

    This API object provides the ability to list, get, add, modify, etc., the
    objects in the BadgeKit REST API.  The goal is to abstract away as much of
    the network communication as possible, while not including a lot of
    special data about the structure of the API methods.  So, you will still
    need to know which methods can be called on which API endpoints, etc.

    At this point, such a list exists here:
    https://github.com/mozilla/badgekit-api/blob/update-docs/docs/api-endpoints.md

    As an example of translating between that list and this client, the list
    says you can

        GET /systems/:slug/issuers/:slug/programs/:slug/badges/:slug/applications

    With this client, you could say the following to hit that endpoint:

        api.list('application', system=sys, issuer=iss, program=prog, badge=badge)

    Notice that all the parameters are singular forms of the nouns.  The order
    of the method parameters does not matter, they are pulled into order when the
    URL is constructed.
    """
    def __init__(self, baseurl, secret, key='master'):
        self.baseurl = baseurl

        auth = jwt_auth.JWTAuth(secret)
        auth.add_field('key', key)
        auth.expire(30)
        auth.add_field('path', jwt_auth.payload_path)
        auth.add_field('method', jwt_auth.payload_method)
        auth.add_field('body', jwt_auth.payload_body)
        self.auth = auth

    def ping(self):
        "Tests the server's availability"
        resp = requests.get(urljoin(self.baseurl, '/'), auth=self.auth)
        resp_dict = json.loads(resp.text)
        return resp.status_code == 200 and resp_dict['app'] == 'BadgeKit API'

    def list(self, kind, **kwargs):
        """
        Lists objects present in some container or badge.

        >>> bk.list('badge', system='mysystem')
        [ ... ]

        The first argument is the kind of object that you would like to list.
        All other arguments should be keywords specifying the location of that
        object, for instance the system, issuer, and program.
        """
        kind_plural = _api_plural(kind)
        path = _make_path(kind_plural, **kwargs)
        resp = requests.get(urljoin(self.baseurl, path), auth=self.auth)
        resp_obj = json.loads(resp.text)
        if resp.status_code != 200:
            raise_error(resp_obj)
        return resp_obj[kind_plural]

    def get(self, **kwargs):
        """
        Retrieves some object from the API.

        >>> bk.get(system='mysystem', badge='stupendous-badge')
        { ... }

        The arguments should all be keywords, specifying the location of
        the object.
        """
        path = _make_path(**kwargs)
        resp = requests.get(urljoin(self.baseurl, path), auth=self.auth)
        resp_obj = json.loads(resp.text)
        if resp.status_code != 200:
            raise_error(resp_obj)

        keys = resp_obj.keys()
        if len(keys) == 1:
            return resp_obj[keys[0]]
        else:
            # ???
            return resp_obj

    def create(self, data, **kwargs):
        "Create an object"
        raise NotImplementedError()

    def update(self, data, **kwargs):
        "Update an object"
        raise NotImplementedError()

    def delete(self, **kwargs):
        "Delete an object"
        raise NotImplementedError()
