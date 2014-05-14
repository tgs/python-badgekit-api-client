import requests
import posixpath
from . import jwt_auth
try:
    from urlparse import urljoin
    from urllib import urlencode
except ImportError:
    from urllib.parse import urljoin, urlencode
import json
import collections
from requests.exceptions import RequestException


__all__ = [
        'BadgeKitException',
        'RequestException',
        'APIError',
        'ResourceNotFound',
        'ResourceConflict',
        'BadgeKitAPI',
        ]


class BadgeKitException(Exception):
    pass

class APIError(BadgeKitException):
    "Thrown for unexpected problems, maybe problems in this library"

class CodedBadgeKitException(BadgeKitException):
    def __init__(self, resp_obj, request):
        self.info = resp_obj
        self.request = request

    def __str__(self):
        return "{class}: {method} {url} returned {code}: {message}".format(
                **{
                    'class': type(self).__name__,
                    'method': self.request.method,
                    'url': self.request.url,
                    'code': self.info.get('code'),
                    'message': self.info.get('message'),
                })

class ResourceNotFound(CodedBadgeKitException):
    "Thrown for HTTP 404 when it is meaningful for the API"

class ResourceConflict(CodedBadgeKitException):
    "Thrown when POSTing an item that already exists"


errors = {
        'ResourceNotFound': ResourceNotFound,
        'ResourceConflict': ResourceConflict,
        }

def raise_error(resp_obj, request):
    try:
        # Find a specific exception for this code, if it exists
        exc_type = errors[resp_obj['code']]

        # test that the response includes a 'message' and a 'code'
        resp_obj['message']
        resp_obj['code']
    except:
        raise APIError(
                "Problem with %s %s, and Badgekit-API didn't return a comprehensible error." \
                        % (request.method, request.url))

    raise exc_type(resp_obj, request)


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
    if noun not in ['evidence', 'claim', 'codes/random']:
        return noun + 's'
    else:
        return noun


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
                urlencode(params))
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
        """
        Returns a new BadgeKitAPI object.

        :param baseurl: the URL of the badgekit-api server.
        :param secret: the client secret.
        :param key: the name of the client secret, for the server to see.

        For the moment, the secret is just the same secret that is used between
        the two Node.js servers, badgekit-api and openbadges-badgekit.  Look
        for it in the environment variables of the badgekit-api server - maybe
        a file called `.env`.
        """
        self.baseurl = baseurl

        auth = jwt_auth.JWTAuth(secret)
        auth.add_field('key', key)
        auth.expire(30)
        auth.add_field('path', jwt_auth.payload_path)
        auth.add_field('method', jwt_auth.payload_method)
        auth.add_field('body', jwt_auth.payload_body)
        self.auth = auth

    def ping(self):
        """Tests the server's availability - returns True if
        server is available, False otherwise."""
        try:
            resp = requests.get(urljoin(self.baseurl, '/'), auth=self.auth)
            resp_dict = self._json_loads(resp.text)
            return resp.status_code == 200 and resp_dict['app'] == 'BadgeKit API'
        except requests.ConnectionError:
            return False

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
        resp_obj = self._json_loads(resp.text)
        if resp.status_code != 200:
            raise_error(resp_obj, resp.request)
        return resp_obj

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
        resp_obj = self._json_loads(resp.text)

        if resp.status_code != 200:
            raise_error(resp_obj, resp.request)

        return resp_obj

    def create(self, kind, data, **kwargs):
        "Create an object"
        path = _make_path(_api_plural(kind), **kwargs)
        resp = requests.post(urljoin(self.baseurl, path),
                data=data,
                auth=self.auth)
        resp_obj = self._json_loads(resp.text)

        if resp.status_code != 201:
            raise_error(resp_obj, resp.request)

        return resp_obj

    def update(self, data, **kwargs):
        "Update an object - not implemented yet"
        raise NotImplementedError()

    def delete(self, **kwargs):
        "Delete an object - not implemented yet"
        raise NotImplementedError()

    def _json_loads(self, text):
        try:
            return json.loads(text)
        except ValueError as e:
            raise APIError("Invalid JSON in BadgeKit response")
