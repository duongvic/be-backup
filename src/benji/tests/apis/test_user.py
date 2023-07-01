import json
import requests

from benji.tests import CustomTestcase

from benji.tests.apis import meta


class TestUser(CustomTestcase):

    def setUp(self) -> None:
        pass

    def test_require_login_params(self):
        body = meta.USER_LOGIN_REQ
        self.assertIsNot(body, 'user_name')
        self.assertIsNot(body, 'password')

    def test_login(self):
        r = requests.post('{}/login'.format(meta.API_URL),
                          data=json.dumps(meta.USER_LOGIN_REQ),
                          headers=meta.HEADER)
        self.assertEqual(r.status_code, 200)
        r_json = r.json()
        self.assertIsNotNone(r_json['access_token'])
