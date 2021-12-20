from app import app
import unittest


class TestModels(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client(self)

    def test_delete(self):
        response = self.client.get('/delete?name=some_name')
        self.assertEqual(response.status_code, 200)

    def test_get_models(self):
        response = self.client.get('/get_models?user=123456')
        self.assertEqual(response.status_code, 200)