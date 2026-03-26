from django.test import TestCase, Client
from unittest.mock import patch
from populate_script import add_user

# Create your tests here.
class SearchTests(TestCase):
    def test_empty_query(self):
        c = Client()
        resp = c.get("/search/?query=")
        self.assertEqual(resp.status_code, 302)

    def test_empty_type(self):
        c = Client()
        resp = c.get("/search/?query=justthis&type=")
        self.assertEqual(resp.status_code, 302)

    def test_empty_order(self):
        c = Client()
        resp = c.get("/search/?query=justthis&type=profile&order=")
        self.assertEqual(resp.status_code, 200)

    def test_missing_query(self):
        c = Client()
        resp = c.get("/search/?type=profile")
        self.assertEqual(resp.status_code, 302)

    def test_missing_type(self):
        c = Client()
        resp = c.get("/search/?query=justthis")
        self.assertEqual(resp.status_code, 302)

    def test_missing_order(self):
        c = Client()
        resp = c.get("/search/?query=justthis&type=profile")
        self.assertEqual(resp.status_code, 200)

    def test_invalid_type(self):
        c = Client()
        resp = c.get("/search/?query=justthis&type=notarealtype")
        self.assertEqual(resp.status_code, 302)

    def test_invalid_order(self):
        c = Client()
        resp = c.get("/search/?query=justthis&type=profile&order=fakeorder")
        self.assertEqual(resp.status_code, 200)

    def check_no_result():
        c = Client()
        resp = c.get("/search/?query=JohnUnreal&type=profile")
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, '<div class="item"></div>')
        self.assertContains(resp, "<h2>These things happen...</h2>")
        self.assertContains(resp, "<p>Your query seems to have no results.</p>")

    def check_for_results():
        c = Client()
        resp = c.get("/search/?query=JaneSampleson&type=profile")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, '<div class="item"></div>')
        self.assertNotContains(resp, "<h2>These things happen...</h2>")
        self.assertNotContains(resp, "<p>Your query seems to have no results.</p>")
