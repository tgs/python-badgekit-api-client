import unittest
import query

class BadgeKitQueryTest(unittest.TestCase):
    def test_blah(self):
        self.assert_(True)

    def test_container(self):
        c = query.ContainerQuery(system='badgekit')
        self.assertEqual(c.path(), 'systems/badgekit')

    def test_container_fluent(self):
        c = query.ContainerQuery('sys')
        self.assertEqual(c.path(), 'systems/sys')
        c2 = c.issuer('issu')
        self.assertNotEqual(c, c2) # TODO I think this is the right design...
        self.assertEqual(c2.path(), 'systems/sys/issuers/issu')



