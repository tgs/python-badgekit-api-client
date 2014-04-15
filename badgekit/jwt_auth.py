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

def exp_after(secs):
    return lambda req: str(int(time.time() + secs))

payload_method = lambda req: req.method
payload_path = lambda req: req.path_url

def default_payload():
    return {
        'method': payload_method,
        'path': payload_path,
        }

class JWSAuth(AuthBase):
    def __init__(self, secret, payload=default_payload(), alg='HS256'):
        """
        Create a client object that will sign requests with JSON Web Tokens.
        """
        # TODO add exp (expire)
        self.secret = secret
        self.alg = alg
        self.payload_generators = payload

    def __call__(self, request):
        payload = {}
        for field, gen in self.payload_generators.iteritems():
            value = None
            if callable(gen):
                value = gen(request)
            else:
                value = gen

            if value:
                payload[field] = value
        token = to_jwt(payload, self.alg, self.secret)
    
        request.headers['Authorization'] = 'JWT token="%s"' % token
        return request

