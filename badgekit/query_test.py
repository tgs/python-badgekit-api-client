import unittest
import query

class BadgeKitQueryTest(unittest.TestCase):
    def test_blah(self):
        self.assert_(True)

    def test_collection(self):
        c = query.CollectionQuery(system='badgekit')
        self.assertEqual(c.url(), 'systems/badgekit')

    def test_coll_fluent(self):
        c = query.CollectionQuery('sys')
        self.assertEqual(c.url(), 'systems/sys')
        c2 = c.issuer('issu')
        self.assertNotEqual(c, c2) # TODO I think this is the right design...
        self.assertEqual(c2.url(), 'systems/sys/issuers/issu')



