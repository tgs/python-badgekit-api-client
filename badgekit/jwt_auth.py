import requests
import hashlib
from requests.auth import AuthBase
import time
import jws

# From https://github.com/brianloveswords/python-jws/blob/master/examples/minijwt.py
def to_jwt(claim, algo, key):
    header = {'typ': 'JWT', 'alg': algo}
    return '.'.join([
        jws.utils.encode(header),
        jws.utils.encode(claim),
        jws.sign(header, claim, key),
    ])


payload_method = lambda req: req.method
payload_path = lambda req: req.path_url


def payload_body(req):
    if req.method in ('POST', 'PUT'):
        return {
                'hash': hashlib.sha256(req.body).hexdigest(),
                'alg': 'sha256',
                }


class JWTAuth(AuthBase):
    """
    An Authorization/Authentication system for requests, implementing JSON Web Tokens.

    The basic usage is this:

        auth = JWTAuth(secret)
        resp = requests.get('http://example.com/', auth=auth)

    You can add fields to the signed payload using the expire() and add_field() methods.
    """
    def __init__(self, secret, alg='HS256'):
        """
        Create a client object that will sign requests with JSON Web Tokens.
        """
        self.secret = secret
        self.alg = alg
        self._generators = {}

    def add_field(self, name, generator):
        """
        Add a field to the JWT payload.

         - name: The name of the field.  Should be a string.
         - generator: a value or generator, the value of the field.

        If `generator` is callable, then each time a request is made with
        this JWTAuth, the generator will be called with one argument: the
        request.  For instance, here is field that will have your JWT
        sign the path that it is requesting:

            auth.add_field('path', lambda req: req.path_url)

        If `generator` is not callable, it will be included directly in the
        JWT payload.  It could be a string or a JSON-serializable object.
        """
        self._generators[name] = generator

    def expire(self, secs):
        """
        Adds the standard 'exp' field, used to prevent replay attacks.

        Adds the 'exp' field to the payload.  When a request is made,
        the field says that it should expire at now + `secs` seconds.

        Of course, this provides no protection unless the server reads
        and interprets this field.
        """
        self.add_field('exp',
                lambda req: str(int(time.time() + secs)))

    def _generate(self, request):
        "Generate a payload for the given request."
        payload = {}
        for field, gen in self._generators.iteritems():
            value = None
            if callable(gen):
                value = gen(request)
            else:
                value = gen

            if value:
                payload[field] = value
        return payload

    def __call__(self, request):
        "Called by requests when a request is made."
        payload = self._generate(request)
        token = to_jwt(payload, self.alg, self.secret)
    
        request.headers['Authorization'] = 'JWT token="%s"' % token
        return request
