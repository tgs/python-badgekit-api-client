import requests
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

class JWTAuth(AuthBase):
    def __init__(self, secret, alg='HS256'):
        """
        Create a client object that will sign requests with JSON Web Tokens.
        """
        # TODO add exp (expire)
        self.secret = secret
        self.alg = alg
        self._generators = {}

    def add_field(self, name, generator):
        self._generators[name] = generator

    def expire(self, secs):
        self.add_field('exp',
                lambda req: str(int(time.time() + secs)))

    def generate(self, request):
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
        payload = self.generate(request)
        token = to_jwt(payload, self.alg, self.secret)
    
        request.headers['Authorization'] = 'JWT token="%s"' % token
        return request
