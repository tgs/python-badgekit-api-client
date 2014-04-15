import posixpath
from urllib import quote_plus

class BadgeKitQuery(object):
    pass

class ContainerQuery(BadgeKitQuery):
    def __init__(self, system, issuer=None, program=None):
        if system is None:
            raise ValueError('Must have at least a System for a valid collection')
        self._system = system
        self._issuer = issuer
        self._program = program

    def system(self, system):
        "Return a new query, with a replaced Badge System"
        return ContainerQuery(system, self._issuer, self._program)

    def issuer(self, issuer):
        "Return a new query, with a replaced Issuer"
        return ContainerQuery(self._system, issuer, self._program)

    def program(self, program):
        "Return a new query, with a replaced Program"
        return ContainerQuery(self._system, self._issuer, program)

    def url(self):
        parts = []
        parts.extend(['systems', self._system])
        if self._issuer is not None:
            parts.extend(['issuers', self._issuer])
        if self._program is not None:
            parts.extend(['programs', self._program])

        return posixpath.join(*list(quote_plus(part) for part in parts))




