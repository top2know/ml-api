from app import app
import unittest


class TestAPI(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client(self)

    def test_datasets_list(self):
        response = self.client.get('/datasets/list')
        self.assertEqual(response.status_code, 200)

    def test_get_models(self):
        response = self.client.get('/models/types_list')
        self.assertEqual(response.status_code, 200)