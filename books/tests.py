from django.test import TestCase, Client
from unittest.mock import patch

import olapi.main
from olapi.ol_api_helpers import subject_filterer, rename_field, strip_book_data, strip_search_result_data, validate_workid
from populate_script import add_user, add_review, add_book
import json

# Create your tests here.

class OlApiMainTests(TestCase):
    """
    Tests of the OLAPI main functions.
    """
    # Tests for the cover_from_workid function.
    @patch("olapi.main.fetch_from_workid")
    def test_no_cover_when_no_book(self, mock_fetch):
        mock_fetch.return_value = None
        cover = olapi.main.cover_from_workid("OL82586W")
        self.assertEqual(cover, None)

    @patch("olapi.main.fetch_from_workid")
    def test_no_cover_when_book_without_cover(self, mock_fetch):
        mock_fetch.return_value = {
                "workid": "OL1W",
                "title": "Sample Book",
                "authors": ["Jane Sampleson"],
                "first_publish_date": "2000",
                "covers": None,
                "subjects": ["Sample", "Testing"]
                }
        cover = olapi.main.cover_from_workid("OL1W")
        self.assertEqual(cover, None)

    @patch("olapi.main.fetch_from_workid")
    def test_thumbnail_working(self, mock_fetch):
        mock_fetch.return_value = {
                "workid": "OL1W",
                "title": "Sample Book",
                "authors": ["Jane Sampleson"],
                "first_publish_date": "2000",
                "covers": "1",
                "subjects": ["Sample", "Testing"]
                }
        cover = olapi.main.cover_from_workid("OL1W")
        self.assertEqual(cover, "https://covers.openlibrary.org/b/id/1-M.jpg")

    @patch("olapi.main.fetch_from_workid")
    def test_non_thumbnail_working(self, mock_fetch):
        mock_fetch.return_value = {
                "workid": "OL1W",
                "title": "Sample Book",
                "authors": ["Jane Sampleson"],
                "first_publish_date": "2000",
                "covers": "1",
                "subjects": ["Sample", "Testing"]
                }
        cover = olapi.main.cover_from_workid("OL1W", is_thumbnail=False)
        self.assertEqual(cover, "https://covers.openlibrary.org/b/id/1-L.jpg")

class OlApiHelperTests(TestCase):
    def test_invalid_workids(self):
        bogus_workids = ["123", "OLookitsnotaworkid", "OLW", "AL1W", "A123W", "", "OL"]
        self.assertFalse((True in [validate_workid(fake_id) for fake_id in bogus_workids]))

    def test_non_ascii_genres_removed(self):
        genres = ["🐟", "that's a 鱼", "físh"]
        genres = subject_filterer(genres)
        self.assertTrue(len(genres) == 0)

    def test_numeric_genres_removed(self):
        genres = ["000", "123", "I sh0uldn't survive", "100 percent not making it", "99 birds 98 fell"]
        genres = subject_filterer(genres)
        self.assertTrue(len(genres) == 0)

    def test_punctuation_genres_removed(self):
        genres = ["This should be removed.", "This, too", "well: that's gone", "y.e.p.", "thats_right", "(and this)"]
        genres = subject_filterer(genres)
        self.assertTrue(len(genres) == 0)

    def test_field_rename_working(self):
        sample_rename_dict = {
                "old": "Value",
                }

        after_rename = {
                "new": "Value",
                }

        rename_field(sample_rename_dict, "old", "new")
        self.assertTrue(sample_rename_dict == after_rename)

    def test_search_result_correctly_formatted(self):
        sample_search_result = {
                "title": "some book",
                "author_name": ["author 1", "author 2"],
                "first_publish_year": "1987",
                "cover_i": "111",
                "key": "OL111W"
                }

        should_return = {
                "title": "some book",
                "authors": ["author 1", "author 2"],
                "first_publish_date": "1987",
                "cover": "https://covers.openlibrary.org/b/id/111-M.jpg",
                "workid": "OL111W",
                "cover_i": "111"
                }

        self.assertTrue(strip_search_result_data(sample_search_result) == should_return)

    def test_malformed_search_result_ok(self):
        sample_malformed = {
                "okay": "this is nothing like a normal search",
                "wrong fields": "and there's nothing really correct here",
                }

        should_return = {
                "workid": None,
                "title": None,
                "authors": None,
                "first_publish_date": None,
                "cover": None,
                "cover_i": None
                }
        self.assertTrue(strip_search_result_data(sample_malformed) == should_return)


class BookViewTests(TestCase):
    """
    Whichever book view tests are possible to do on Django's end (pretty much just reviews)
    """
    def test_reviewed_book_shows_reviews(self):
        "Checks if a book with reviews shows its reviews."
        add_book("OL1W", "Sample Book", "Jane Sampleson")
        add_user("JaneSampleson")
        add_review("As an unbiased third party this book is great!", 5, "JaneSampleson", "OL1W")
        c = Client()
        resp = c.get('/books/OL1W/')
        self.assertEqual(resp.status_code, 200, f"page doesnt exist")
        self.assertContains(resp, '<div class="review">')

    def test_unreviewed_book_shows_no_reviews(self):
        "Checks if the view for a book with no reviews says it has no reviews."
        c = Client()
        resp = c.get('/books/OL2W/')
        self.assertEqual(resp.status_code, 200, f"page doesnt exist")
        self.assertNotContains(resp, '<div class="review">')
        self.assertContains(resp, "<p>No reviews yet.</p>")
