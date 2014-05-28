#!/usr/bin/env python
import unittest


# Load all test modules - add more here
all_modules = []
from . import api_test
all_modules.append(api_test)


def suite():
    suite = unittest.TestSuite()

    for mod in all_modules:
        suite.addTests(
                unittest.defaultTestLoader.loadTestsFromModule(mod))

    return suite
