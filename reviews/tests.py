"""
Tests for the reviews app: models, URL routing, views, and edge cases.

If `python manage.py test reviews` fails while applying migrations (duplicate
reviews 0002_* branches), use:

    DJANGO_SETTINGS_MODULE=bookhive.settings_test python manage.py test reviews
"""
from datetime import timedelta
from unittest.mock import patch

from django.apps import apps
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import Client, TestCase
from django.urls import resolve, reverse
from django.utils import timezone

from books.models import Book
from reviews import views as reviews_views
from reviews.apps import ReviewsConfig
from reviews.models import Favourite, Review


def _api_payload():
    return {
        "title": "Test Book",
        "authors": ["Author One", "Author Two"],
        "first_publish_date": "1999-01-01",
        "subjects": ["fiction"],
    }


MOCK_COVER_URL = "https://example.com/cover.jpg"


def with_successful_olapi(api_payload=None, *, cover_url=MOCK_COVER_URL):
    """Patch `fetch_from_workid` and `cover_from_workid` with successful defaults."""

    data = _api_payload() if api_payload is None else api_payload

    def decorator(test_method):
        return patch(
            "reviews.views.cover_from_workid", return_value=cover_url
        )(
            patch(
                "reviews.views.fetch_from_workid", return_value=data
            )(test_method)
        )

    return decorator


class BookReviewsViewTests(TestCase):
    """Integration-style tests for book_reviews; olapi is mocked."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="reviewer", password="test-pass-123"
        )
        self.work_id = "ol82586w"
        self.url = reverse("book_reviews", kwargs={"work_id": self.work_id})

    def _login_reviewer(self):
        self.client.login(username="reviewer", password="test-pass-123")

    @patch("reviews.views.cover_from_workid", return_value=MOCK_COVER_URL)
    @patch("reviews.views.fetch_from_workid", side_effect=RuntimeError("network"))
    def test_redirects_to_index_when_open_library_fetch_fails(
        self, _mock_fetch, _mock_cover
    ):
        self._login_reviewer()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("index"))

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    @with_successful_olapi()
    def test_get_creates_book_and_renders_reviews_template(self, _mock_fetch, _mock_cover):
        self._login_reviewer()
        self.assertFalse(Book.objects.filter(hardcover_id=self.work_id).exists())

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reviews/reviews.html")
        book = Book.objects.get(hardcover_id=self.work_id)
        self.assertEqual(book.title, "Test Book")
        self.assertEqual(book.author, "Author One, Author Two")
        self.assertEqual(response.context["work_id"], self.work_id)
        self.assertEqual(response.context["book"], book)
        self.assertEqual(response.context["title"], "Test Book")
        self.assertTrue(response.context["show_review_form"])

    @with_successful_olapi()
    def test_existing_review_hides_form_unless_edit_query_param(
        self, _mock_fetch, _mock_cover
    ):
        self._login_reviewer()
        self.client.get(self.url)
        book = Book.objects.get(hardcover_id=self.work_id)
        Review.objects.create(
            reviewer=self.user,
            book=book,
            rating=4,
            comment="Already reviewed.",
        )

        response_default = self.client.get(self.url)
        self.assertFalse(response_default.context["show_review_form"])

        response_edit = self.client.get(self.url, {"edit": "1"})
        self.assertTrue(response_edit.context["show_review_form"])

    @with_successful_olapi()
    def test_post_creates_review_and_redirects_back(self, _mock_fetch, _mock_cover):
        self._login_reviewer()
        self.client.get(self.url)
        book = Book.objects.get(hardcover_id=self.work_id)

        response = self.client.post(
            self.url,
            {"comment": "Great read.", "rating": "5"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.url)
        review = Review.objects.get(book=book, reviewer=self.user)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, "Great read.")

    @with_successful_olapi()
    def test_post_updates_existing_review_instead_of_duplicating(
        self, _mock_fetch, _mock_cover
    ):
        self._login_reviewer()
        self.client.get(self.url)
        book = Book.objects.get(hardcover_id=self.work_id)
        Review.objects.create(
            reviewer=self.user,
            book=book,
            rating=2,
            comment="First draft.",
        )

        self.client.post(
            self.url,
            {"comment": "Updated thoughts.", "rating": "4"},
        )

        self.assertEqual(Review.objects.filter(book=book, reviewer=self.user).count(), 1)
        review = Review.objects.get(book=book, reviewer=self.user)
        self.assertEqual(review.rating, 4)
        self.assertEqual(review.comment, "Updated thoughts.")

    @with_successful_olapi()
    def test_post_invalid_rating_uses_existing_then_clamps_to_valid_range(
        self, _mock_fetch, _mock_cover
    ):
        self._login_reviewer()
        self.client.get(self.url)
        book = Book.objects.get(hardcover_id=self.work_id)
        Review.objects.create(
            reviewer=self.user,
            book=book,
            rating=3,
            comment="Baseline.",
        )

        self.client.post(
            self.url,
            {"comment": "Still invalid rating field.", "rating": "not-a-number"},
        )
        review = Review.objects.get(book=book, reviewer=self.user)
        self.assertEqual(review.rating, 3)

        self.client.post(
            self.url,
            {"comment": "Clamped high.", "rating": "99"},
        )
        review.refresh_from_db()
        self.assertEqual(review.rating, 5)

        self.client.post(
            self.url,
            {"comment": "Clamped low.", "rating": "-10"},
        )
        review.refresh_from_db()
        self.assertEqual(review.rating, 1)

    @patch("reviews.views.cover_from_workid", side_effect=OSError("cover unavailable"))
    @patch("reviews.views.fetch_from_workid", return_value=_api_payload())
    def test_redirects_to_index_when_cover_fetch_fails_but_metadata_ok(
        self, _mock_fetch, _mock_cover
    ):
        self._login_reviewer()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("index"))

    @with_successful_olapi()
    def test_post_empty_or_whitespace_comment_does_not_save_or_redirect(
        self, _mock_fetch, _mock_cover
    ):
        self._login_reviewer()
        self.client.get(self.url)

        for body in (
            {"comment": "", "rating": "5"},
            {"comment": "   \t  ", "rating": "4"},
        ):
            with self.subTest(body=body):
                response = self.client.post(self.url, body)
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, "reviews/reviews.html")
                self.assertFalse(
                    Review.objects.filter(reviewer=self.user).exists()
                )

    @with_successful_olapi()
    def test_edit_query_accepts_true_yes_on(self, _mock_fetch, _mock_cover):
        self._login_reviewer()
        self.client.get(self.url)
        book = Book.objects.get(hardcover_id=self.work_id)
        Review.objects.create(
            reviewer=self.user,
            book=book,
            rating=3,
            comment="Done.",
        )
        for value in ("true", "yes", "on"):
            with self.subTest(edit=value):
                r = self.client.get(self.url, {"edit": value})
                self.assertTrue(r.context["show_review_form"])

    @with_successful_olapi()
    def test_edit_query_unrecognized_value_hides_form_when_review_exists(
        self, _mock_fetch, _mock_cover
    ):
        self._login_reviewer()
        self.client.get(self.url)
        book = Book.objects.get(hardcover_id=self.work_id)
        Review.objects.create(
            reviewer=self.user,
            book=book,
            rating=3,
            comment="Done.",
        )
        response = self.client.get(self.url, {"edit": "maybe"})
        self.assertFalse(response.context["show_review_form"])

    @with_successful_olapi()
    def test_post_updates_every_duplicate_review_row_for_user(
        self, _mock_fetch, _mock_cover
    ):
        self._login_reviewer()
        self.client.get(self.url)
        book = Book.objects.get(hardcover_id=self.work_id)
        Review.objects.create(
            reviewer=self.user,
            book=book,
            rating=1,
            comment="older duplicate",
        )
        Review.objects.create(
            reviewer=self.user,
            book=book,
            rating=1,
            comment="newer duplicate",
        )

        self.client.post(
            self.url,
            {"comment": "Single canonical text.", "rating": "5"},
        )

        rows = Review.objects.filter(book=book, reviewer=self.user).order_by("id")
        self.assertEqual(rows.count(), 2)
        for row in rows:
            self.assertEqual(row.comment, "Single canonical text.")
            self.assertEqual(row.rating, 5)

    @with_successful_olapi()
    def test_new_review_invalid_or_missing_rating_defaults_to_three(
        self, _mock_fetch, _mock_cover
    ):
        self._login_reviewer()
        self.client.get(self.url)
        book = Book.objects.get(hardcover_id=self.work_id)

        self.client.post(
            self.url,
            {"comment": "No valid rating.", "rating": "not-int"},
        )
        r1 = Review.objects.get(book=book, reviewer=self.user)
        self.assertEqual(r1.rating, 3)

        r1.delete()
        self.client.post(
            self.url,
            {"comment": "Missing rating key.", "rating": ""},
        )
        r2 = Review.objects.get(book=book, reviewer=self.user)
        self.assertEqual(r2.rating, 3)

    @with_successful_olapi()
    def test_get_context_includes_cover_authors_dates_and_subjects(
        self, _mock_fetch, _mock_cover
    ):
        self._login_reviewer()
        response = self.client.get(self.url)
        self.assertEqual(response.context["cover"], MOCK_COVER_URL)
        self.assertEqual(
            response.context["authors"], ["Author One", "Author Two"]
        )
        self.assertEqual(response.context["first_publish_date"], "1999-01-01")
        self.assertEqual(response.context["subjects"], ["fiction"])

    @with_successful_olapi()
    def test_reviews_queryset_newest_first_in_template_context(
        self, _mock_fetch, _mock_cover
    ):
        other = User.objects.create_user(username="other", password="x")
        self._login_reviewer()
        self.client.get(self.url)
        book = Book.objects.get(hardcover_id=self.work_id)

        older = Review.objects.create(
            reviewer=self.user,
            book=book,
            rating=3,
            comment="Older",
        )
        Review.objects.filter(pk=older.pk).update(
            created_at=timezone.now() - timedelta(days=2)
        )
        newer = Review.objects.create(
            reviewer=other,
            book=book,
            rating=4,
            comment="Newer",
        )

        response = self.client.get(self.url)
        ctx_reviews = list(response.context["reviews"])
        self.assertEqual(ctx_reviews[0], newer)
        self.assertEqual(ctx_reviews[1], older)

    @with_successful_olapi()
    def test_existing_review_context_is_latest_row_when_duplicates_exist(
        self, _mock_fetch, _mock_cover
    ):
        self._login_reviewer()
        self.client.get(self.url)
        book = Book.objects.get(hardcover_id=self.work_id)
        first = Review.objects.create(
            reviewer=self.user,
            book=book,
            rating=2,
            comment="First row",
        )
        Review.objects.filter(pk=first.pk).update(
            created_at=timezone.now() - timedelta(days=1)
        )
        second = Review.objects.create(
            reviewer=self.user,
            book=book,
            rating=3,
            comment="Second row",
        )

        response = self.client.get(self.url)
        self.assertEqual(response.context["existing_review"], second)

    @with_successful_olapi()
    def test_get_or_create_does_not_overwrite_existing_book_row(
        self, _mock_fetch, _mock_cover
    ):
        Book.objects.create(
            hardcover_id=self.work_id,
            title="Already Here",
            author="Someone",
        )
        self._login_reviewer()
        self.client.get(self.url)
        book = Book.objects.get(hardcover_id=self.work_id)
        self.assertEqual(book.title, "Already Here")
        self.assertEqual(book.author, "Someone")

    @with_successful_olapi({})
    def test_minimal_api_payload_defaults_title_and_author(self, _mock_fetch, _mock_cover):
        self._login_reviewer()
        self.client.get(self.url)
        book = Book.objects.get(hardcover_id=self.work_id)
        self.assertEqual(book.title, "Unknown")
        self.assertEqual(book.author, "")

    def test_anonymous_post_redirects_to_login(self):
        response = self.client.post(
            self.url,
            {"comment": "Spam", "rating": "5"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)


class ReviewModelTests(TestCase):
    def test_str_uses_book_title_and_username(self):
        user = User.objects.create_user(username="alice", password="x")
        book = Book.objects.create(
            hardcover_id="b1", title="Moby Dick", author="Melville"
        )
        review = Review.objects.create(
            reviewer=user, book=book, rating=5, comment="Epic."
        )
        self.assertEqual(str(review), "Moby Dick - alice")

    def test_book_related_name_returns_reviews(self):
        user = User.objects.create_user(username="bob", password="x")
        book = Book.objects.create(
            hardcover_id="b2", title="Dune", author="Herbert"
        )
        Review.objects.create(
            reviewer=user, book=book, rating=4, comment="Sand."
        )
        self.assertEqual(book.reviews.count(), 1)
        self.assertEqual(book.reviews.first().comment, "Sand.")


class FavouriteModelTests(TestCase):
    def test_str_includes_username_and_book_title(self):
        user = User.objects.create_user(username="carol", password="x")
        book = Book.objects.create(
            hardcover_id="b3", title="1984", author="Orwell"
        )
        fav = Favourite.objects.create(user=user, book=book)
        self.assertEqual(str(fav), "carol's favourite: 1984")

    def test_unique_together_user_and_book(self):
        user = User.objects.create_user(username="dave", password="x")
        book = Book.objects.create(
            hardcover_id="b4", title="Emma", author="Austen"
        )
        Favourite.objects.create(user=user, book=book)
        with self.assertRaises(IntegrityError):
            Favourite.objects.create(user=user, book=book)

    def test_deleted_user_removes_favourites(self):
        user = User.objects.create_user(username="erin", password="x")
        book = Book.objects.create(
            hardcover_id="b5", title="Persuasion", author="Austen"
        )
        Favourite.objects.create(user=user, book=book)
        user.delete()
        self.assertEqual(Favourite.objects.count(), 0)


class ReviewsUrlsTests(TestCase):
    def test_book_reviews_reverse_and_resolve(self):
        url = reverse("book_reviews", kwargs={"work_id": "ol123w"})
        self.assertEqual(url, "/reviews/ol123w/")
        match = resolve(url)
        self.assertEqual(match.func, reviews_views.book_reviews)
        self.assertEqual(match.kwargs["work_id"], "ol123w")


class ReviewsAppConfigTests(TestCase):
    def test_reviews_app_registered_with_expected_config(self):
        config = apps.get_app_config("reviews")
        self.assertIsInstance(config, ReviewsConfig)
        self.assertEqual(config.name, "reviews")
