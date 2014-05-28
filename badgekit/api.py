"""
A low-level interface to the BadgeKit API.

The :class:`BadgeKitAPI` object provides the ability to list, get, add, modify,
etc., the objects in the `BadgeKit REST API
<https://github.com/mozilla/badgekit-api>`_.  The goal is to abstract away as
much of the network communication as possible, while not including a lot of
special data about the structure of the API methods.  So, you will still need
to know which methods can be called on which API endpoints, etc.
**At this point, a list of available API endpoints** `exists here
<https://github.com/mozilla/badgekit-api/blob/update-docs/docs/api-endpoints.md>`_.

As an example of translating between that list and this client, the list
says you can

.. code-block:: http

    GET /systems/:slug/issuers/:slug/programs/:slug/badges/:slug/applications HTTP/1.1

With this client, you could say the following to hit that endpoint:

.. code-block:: python

    api.list('application', system=sys, issuer=iss, program=prog, badge=badge)

Notice that all the parameters are singular forms of the nouns.  The order
of the method parameters does not matter, they are pulled into order when the
URL is constructed.

Note that these classes are listed as being part of :mod:`badgekit.api`, but you
can import them straight from :mod:`badgekit`.
"""


import requests
import posixpath
import requests_jwt
from distutils.version import StrictVersion
try:
    from urlparse import urljoin
    from urllib import urlencode
except ImportError:
    from urllib.parse import urljoin, urlencode
import json
import collections
from requests.exceptions import RequestException


__all__ = [
        'BadgeKitAPI',
        'BadgeKitException',
        'RequestException',
        'APIError',
        'ResourceNotFound',
        'ResourceConflict',
        'ValidationError',
        ]


class BadgeKitException(Exception):
    pass

class APIError(BadgeKitException):
    "Thrown for unexpected problems, maybe problems in this library, or invalid JSON from the server."

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

class ValidationError(CodedBadgeKitException):
    "Thrown when creating an item with improper or missing fields"

    def __str__(self):
        super_str = super(ValidationError, self).__str__()
        bad_fields = ", ".join([det['field'] for det in self.info.get('details', [])])
        return ": ".join([super_str, bad_fields])

errors = {
        'ResourceNotFound': ResourceNotFound,
        'ResourceConflict': ResourceConflict,
        'ValidationError': ValidationError,
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
                "Problem with %s %s: %s"
                        % (request.method, request.url, repr(resp_obj)))

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
    A class representing an interface with the BadgeKit API server.

    :param baseurl: the URL of the badgekit-api server.
    :param secret: the client secret.
    :param key: the name of the client secret, for the server to see.
    :param defaults: a dict of default arguments, which can be overridden by actual arguments to the functions.

    For the moment, the secret is just the same secret that is used between
    the two Node.js servers, badgekit-api and openbadges-badgekit.  Look
    for it in the environment variables of the badgekit-api server - maybe
    a file called `.env`.

    The ``defaults`` argument can be quite useful.  If your code will only have
    to work with one badge system at a time - the badge system is in a configuration
    file, for instance - then you can set it once and then not have to pass extra
    info around to all your code that uses the api:

    >>> bk = BadgeKitAPI('http://api.example.com/', 'secr3t', defaults={'system': 'mysystem'})
    """
    def __init__(self, baseurl, secret, key='master', defaults=None):
        self.baseurl = baseurl

        auth = requests_jwt.JWTAuth(secret)
        auth.add_field('key', key)
        auth.expire(30)
        auth.add_field('path', requests_jwt.payload_path)
        auth.add_field('method', requests_jwt.payload_method)
        auth.add_field('body', requests_jwt.payload_body)
        self.auth = auth

        if defaults:
            self.defaults = dict(defaults)
        else:
            self.defaults = {}

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

        :param kind: The 'kind' of object to list - for example, 'badge' or 'system'.

        >>> bk.list('badge', system='mysystem')
        [ ... ]

        The first argument is the kind of object that you would like to list.
        All other arguments should be keywords specifying the location of that
        object, for instance the system, issuer, and program.

        Use this method to ``GET`` a URL that ends with the name of a 'kind' of object -
        for example, the above code would hit ``/systems/mysystem/badges``.
        """
        kind_plural = _api_plural(kind)
        path_args = dict(self.defaults, **kwargs)
        path = _make_path(kind_plural, **path_args)
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

        Use this method to ``GET`` a URL that ends with an identifier of an
        object, and you just want to get that one object - for example, the
        above code would hit ``/systems/mysystem/badges/stupendous-badge``.
        """
        path_args = dict(self.defaults, **kwargs)
        path = _make_path(**path_args)
        resp = requests.get(urljoin(self.baseurl, path), auth=self.auth)
        resp_obj = self._json_loads(resp.text)

        if resp.status_code != 200:
            raise_error(resp_obj, resp.request)

        return resp_obj

    def create(self, kind, data, **kwargs):
        """
        Create an object in the API.

        :param kind: The kind of object to create - 'badge', 'issuer', 'instance', etc.
        :param data: The data fields of the object, as a dict.

        >>> bk.create('badge', {'name': 'Super', ...}, system='mysystem')
        { ... }

        The remaining keyword arguments specify the future location of the object.

        Use this method to ``POST`` a URL that ends with a kind of object.
        For instance, the above code would post to ``/systems/mysystem/badges`` with
        ``data`` as the body of the request.
        """
        path_args = dict(self.defaults, **kwargs)
        path = _make_path(_api_plural(kind), **path_args)
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

    def server_version(self):
        """Returns the server's reported version as a string."""
        resp = requests.get(urljoin(self.baseurl, '/'), auth=self.auth)
        resp_dict = self._json_loads(resp.text)
        return resp_dict['version']

    def require_server_version(self, required_version):
        """
        Require a certain version of the BadgeKit API Server.

        The BadgeKit-API server is under rapid development.  If you require
        particular features, it makes sense to check the server version so that
        you get "fail-early" behavior from your application.  This method
        checks the supplied ``required_version`` against the server's
        version, parses them with :class:`distutils.version.StrictVersion`, and
        compares them.  If the server version is strictly less than
        ``required_version``, a :class:`ValueError` is raised with an
        informative error message.
        """
        version = self.server_version()
        server_url = self.baseurl
        if StrictVersion(version) < StrictVersion(required_version):
            raise ValueError(
                    ("Version {required_version} or greater "
                    + "of BadgeKit-API server required, but "
                    + "{server_url} is only version {version}.")
                    .format(**locals()))
