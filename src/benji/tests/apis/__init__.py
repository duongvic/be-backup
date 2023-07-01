import requests

import unittest


class CustomTestcase(unittest.TestCase):
    HAS_ATTR_MESSAGE = '{} should have an attribute {}'

    def assertHasAttr(self, obj, attr, message=None):
        if not hasattr(obj, attr):
            if message is not None:
                self.fail(message)
            else:
                self.fail(self.HAS_ATTR_MESSAGE.format(obj, attr))
