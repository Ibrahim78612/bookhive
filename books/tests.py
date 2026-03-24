from django.test import TestCase
from olapi.main import fetch_from_workid, cover_from_workid, fetch_with_title
from olapi.ol_api_helpers import subject_filterer, rename_field, strip_book_data, strip_search_result_data, validate_workid

# Create your tests here.

class OlApiMainTests(TestCase):
    """
    Tests of the OLAPI helper functions.
    """
    # Tests for the cover_from_workid function.
    def no_cover_when_no_book(self):
        pass

    def no_cover_when_book_without_cover(self):
        pass

    def is_thumbnail_working(self):
        pass

    def is_non_thumbnail_working(self):
        pass

    # Tests for the raise_errors flag of fetch_with_workid.
    def check_if_error_raised():
        pass

    def check_if_error_ignored():
        pass

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
        genres = ["This should be removed.", "This, too", "...!", "y.e.p.", "thats_right", "(and this)"]
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
    no_review_book = ""
    has_reviews_book = ""

    def reviewed_book_shows_reviews(self):
        "Checks if a book with reviews shows its reviews."
        pass


    def unreviewed_book_says_no_reviews(self):
        "Checks if the view for a book with no reviews says it has no reviews."
        pass

    def is_ajax_accurate(self):
        "Checks the JSON endpoint used for AJAX against fetch_from_workid to ensure they match"
        pass
