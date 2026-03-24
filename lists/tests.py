from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from books.models import Book
from clubs.models import Club
from lists.models import List


class ListViewsBaseTestCase(TestCase):
    def setUp(self):
        self.password = "strong-pass-123"
        self.owner = User.objects.create_user(username="owner", password=self.password)
        self.other = User.objects.create_user(username="other", password=self.password)
        self.club_owner = User.objects.create_user(username="clubowner", password=self.password)
        self.member = User.objects.create_user(username="member", password=self.password)

        self.book = Book.objects.create(
            hardcover_id="OL100W",
            title="Existing Book",
            author="Known Author",
            year=2020,
        )
        self.other_book = Book.objects.create(
            hardcover_id="OL200W",
            title="Other Book",
            author="Second Author",
            year=2021,
        )

        self.personal_list = List.objects.create(
            user=self.owner,
            name="Personal TBR",
            description="Things to read",
        )
        self.personal_list.books.add(self.book)

        self.club = Club.objects.create(
            name="Sci-Fi Club",
            description="Club desc",
            owner=self.club_owner,
        )
        self.club.members.add(self.club_owner, self.member)

        self.club_list = List.objects.create(
            user=self.club_owner,
            club=self.club,
            name="Club Picks",
            description="Club choices",
        )
        self.club_list.books.add(self.book)

    def login(self, user):
        self.client.force_login(user)


class ListDetailViewTests(ListViewsBaseTestCase):
    def test_list_detail_is_public_for_logged_out_user(self):
        response = self.client.get(reverse("list_detail", args=[self.personal_list.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "lists/list_detail.html")
        self.assertEqual(response.context["list"], self.personal_list)
        self.assertFalse(response.context["can_edit"])
        self.assertContains(response, "Personal TBR")
        self.assertContains(response, "Existing Book")
        self.assertNotContains(response, "Edit this list")
        self.assertNotContains(response, "Delete this list")
        self.assertNotContains(response, "Add Book")

    def test_list_detail_allows_owner_to_edit_personal_list(self):
        self.login(self.owner)

        response = self.client.get(reverse("list_detail", args=[self.personal_list.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["can_edit"])
        self.assertContains(response, "Edit this list")
        self.assertContains(response, "Delete this list")
        self.assertContains(response, "Add Book")
        self.assertContains(response, "Remove")

    def test_list_detail_disallows_non_owner_from_editing_personal_list(self):
        self.login(self.other)

        response = self.client.get(reverse("list_detail", args=[self.personal_list.id]))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["can_edit"])
        self.assertNotContains(response, "Edit this list")
        self.assertNotContains(response, "Delete this list")
        self.assertNotContains(response, "Add Book")

    def test_list_detail_allows_club_owner_to_edit_club_list(self):
        self.login(self.club_owner)

        response = self.client.get(reverse("list_detail", args=[self.club_list.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["can_edit"])
        self.assertContains(response, "Club Picks")
        self.assertContains(response, "for club Sci-Fi Club")

    def test_list_detail_disallows_club_member_from_editing_club_list(self):
        self.login(self.member)

        response = self.client.get(reverse("list_detail", args=[self.club_list.id]))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["can_edit"])
        self.assertNotContains(response, "Edit this list")
        self.assertNotContains(response, "Delete this list")

    def test_list_detail_returns_404_for_missing_list(self):
        response = self.client.get(reverse("list_detail", args=[999999]))

        self.assertEqual(response.status_code, 404)

    def test_logged_out_post_cannot_add_book(self):
        response = self.client.post(
            reverse("list_detail", args=[self.personal_list.id]),
            {"add_book": "1", "book_id": self.other_book.hardcover_id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            self.personal_list.books.filter(hardcover_id=self.other_book.hardcover_id).exists()
        )

    def test_non_editor_post_cannot_add_book(self):
        self.login(self.other)

        response = self.client.post(
            reverse("list_detail", args=[self.personal_list.id]),
            {"add_book": "1", "book_id": self.other_book.hardcover_id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            self.personal_list.books.filter(hardcover_id=self.other_book.hardcover_id).exists()
        )

    def test_owner_can_add_existing_local_book(self):
        self.login(self.owner)

        response = self.client.post(
            reverse("list_detail", args=[self.personal_list.id]),
            {"add_book": "1", "book_id": self.other_book.hardcover_id},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            self.personal_list.books.filter(hardcover_id=self.other_book.hardcover_id).exists()
        )
        messages = list(response.context["messages"])
        self.assertTrue(any("Added Other Book to the list." in str(m) for m in messages))

    def test_owner_cannot_add_duplicate_book(self):
        self.login(self.owner)

        response = self.client.post(
            reverse("list_detail", args=[self.personal_list.id]),
            {"add_book": "1", "book_id": self.book.hardcover_id},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.personal_list.books.filter(hardcover_id=self.book.hardcover_id).count(),
            1,
        )
        messages = list(response.context["messages"])
        self.assertTrue(any("Book is already in the list." in str(m) for m in messages))

    @patch("lists.views.cover_from_workid", return_value="https://example.com/thumb.jpg")
    @patch(
        "lists.views.fetch_from_workid",
        return_value={
            "title": "Fetched Book",
            "authors": ["Fetched Author"],
            "first_publish_date": 1999,
        },
    )
    def test_owner_can_add_book_fetched_from_openlibrary(self, mock_fetch, mock_cover):
        self.login(self.owner)

        response = self.client.post(
            reverse("list_detail", args=[self.personal_list.id]),
            {"add_book": "1", "book_id": "OLNEWBOOKW"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Book.objects.filter(hardcover_id="OLNEWBOOKW", title="Fetched Book").exists())
        self.assertTrue(self.personal_list.books.filter(hardcover_id="OLNEWBOOKW").exists())
        messages = list(response.context["messages"])
        self.assertTrue(any("Added Fetched Book to the list." in str(m) for m in messages))

    @patch("lists.views.fetch_from_workid", side_effect=Exception("API failed"))
    def test_owner_gets_error_when_remote_book_fetch_fails(self, mock_fetch):
        self.login(self.owner)

        response = self.client.post(
            reverse("list_detail", args=[self.personal_list.id]),
            {"add_book": "1", "book_id": "OLBROKENW"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Book.objects.filter(hardcover_id="OLBROKENW").exists())
        self.assertFalse(self.personal_list.books.filter(hardcover_id="OLBROKENW").exists())
        messages = list(response.context["messages"])
        self.assertTrue(any("Could not fetch that book from OpenLibrary." in str(m) for m in messages))

    def test_post_add_book_without_book_id_does_nothing(self):
        self.login(self.owner)
        before = self.personal_list.books.count()

        response = self.client.post(
            reverse("list_detail", args=[self.personal_list.id]),
            {"add_book": "1", "book_id": ""},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.personal_list.books.count(), before)

    def test_owner_can_remove_book(self):
        self.login(self.owner)

        response = self.client.post(
            reverse("list_detail", args=[self.personal_list.id]),
            {"remove_book": "1", "remove_book_id": self.book.hardcover_id},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.personal_list.books.filter(hardcover_id=self.book.hardcover_id).exists())
        messages = list(response.context["messages"])
        self.assertTrue(any("Removed Existing Book from the list." in str(m) for m in messages))

    def test_owner_gets_error_when_removing_book_not_in_list(self):
        self.login(self.owner)

        response = self.client.post(
            reverse("list_detail", args=[self.personal_list.id]),
            {"remove_book": "1", "remove_book_id": "DOES-NOT-EXIST"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        messages = list(response.context["messages"])
        self.assertTrue(any("Book not in list." in str(m) for m in messages))


class EditListViewTests(ListViewsBaseTestCase):
    def test_edit_list_redirects_logged_out_user_to_login(self):
        response = self.client.get(reverse("edit_list", args=[self.personal_list.id]))

        self.assertRedirects(
            response,
            f"/accounts/login/?next={reverse('edit_list', args=[self.personal_list.id])}",
            fetch_redirect_response=False,
        )

    def test_owner_can_view_edit_form(self):
        self.login(self.owner)

        response = self.client.get(reverse("edit_list", args=[self.personal_list.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "lists/edit_list.html")
        self.assertEqual(response.context["list"], self.personal_list)
        self.assertContains(response, "Personal TBR")

    def test_non_owner_cannot_view_edit_form(self):
        self.login(self.other)

        response = self.client.get(reverse("edit_list", args=[self.personal_list.id]), follow=True)

        self.assertRedirects(response, reverse("list_detail", args=[self.personal_list.id]))
        messages = list(response.context["messages"])
        self.assertTrue(any("You don't have permission to edit this list." in str(m) for m in messages))

    def test_club_owner_can_edit_club_list(self):
        self.login(self.club_owner)

        response = self.client.post(
            reverse("edit_list", args=[self.club_list.id]),
            {"name": "Updated Club Picks", "description": "New description"},
            follow=True,
        )

        self.assertRedirects(response, reverse("list_detail", args=[self.club_list.id]))
        self.club_list.refresh_from_db()
        self.assertEqual(self.club_list.name, "Updated Club Picks")
        self.assertEqual(self.club_list.description, "New description")
        messages = list(response.context["messages"])
        self.assertTrue(any("List updated." in str(m) for m in messages))

    def test_club_member_cannot_edit_club_list(self):
        self.login(self.member)

        response = self.client.post(
            reverse("edit_list", args=[self.club_list.id]),
            {"name": "Hacked Name", "description": "Nope"},
            follow=True,
        )

        self.assertRedirects(response, reverse("list_detail", args=[self.club_list.id]))
        self.club_list.refresh_from_db()
        self.assertEqual(self.club_list.name, "Club Picks")
        messages = list(response.context["messages"])
        self.assertTrue(any("You don't have permission to edit this list." in str(m) for m in messages))

    def test_owner_can_submit_valid_edit(self):
        self.login(self.owner)

        response = self.client.post(
            reverse("edit_list", args=[self.personal_list.id]),
            {"name": "Updated Personal TBR", "description": "Updated description"},
            follow=True,
        )

        self.assertRedirects(response, reverse("list_detail", args=[self.personal_list.id]))
        self.personal_list.refresh_from_db()
        self.assertEqual(self.personal_list.name, "Updated Personal TBR")
        self.assertEqual(self.personal_list.description, "Updated description")
        messages = list(response.context["messages"])
        self.assertTrue(any("List updated." in str(m) for m in messages))

    def test_owner_cannot_submit_blank_name(self):
        self.login(self.owner)

        response = self.client.post(
            reverse("edit_list", args=[self.personal_list.id]),
            {"name": "", "description": "Still here"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.personal_list.refresh_from_db()
        self.assertEqual(self.personal_list.name, "Personal TBR")
        messages = list(response.context["messages"])
        self.assertTrue(any("List name is required." in str(m) for m in messages))


class CreateListViewTests(ListViewsBaseTestCase):
    def test_create_list_redirects_logged_out_user_to_login(self):
        response = self.client.get(reverse("create_list"))

        self.assertRedirects(
            response,
            f"/accounts/login/?next={reverse('create_list')}",
            fetch_redirect_response=False,
        )

    def test_logged_in_user_can_view_create_list_form(self):
        self.login(self.owner)

        response = self.client.get(reverse("create_list"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "lists/create_list.html")
        self.assertContains(response, "Create New List")

    def test_logged_in_user_can_create_list(self):
        self.login(self.owner)

        response = self.client.post(
            reverse("create_list"),
            {"name": "Brand New List", "description": "Fresh description"},
            follow=True,
        )

        created_list = List.objects.get(name="Brand New List")
        self.assertRedirects(response, reverse("list_detail", args=[created_list.id]))
        self.assertEqual(created_list.user, self.owner)
        self.assertEqual(created_list.description, "Fresh description")
        messages = list(response.context["messages"])
        self.assertTrue(any("Created list 'Brand New List'." in str(m) for m in messages))

    def test_logged_in_user_cannot_create_list_with_blank_name(self):
        self.login(self.owner)

        response = self.client.post(
            reverse("create_list"),
            {"name": "", "description": "No title"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(List.objects.filter(description="No title").exists())
        messages = list(response.context["messages"])
        self.assertTrue(any("List name is required." in str(m) for m in messages))


class DeleteListViewTests(ListViewsBaseTestCase):
    def test_delete_list_redirects_logged_out_user_to_login(self):
        response = self.client.get(reverse("delete_list", args=[self.personal_list.id]))

        self.assertRedirects(
            response,
            f"/accounts/login/?next={reverse('delete_list', args=[self.personal_list.id])}",
            fetch_redirect_response=False,
        )

    def test_owner_can_view_delete_confirmation(self):
        self.login(self.owner)

        response = self.client.get(reverse("delete_list", args=[self.personal_list.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "lists/delete_list.html")
        self.assertContains(response, "Are you sure you want to delete the list")

    def test_non_owner_cannot_delete_list(self):
        self.login(self.other)

        response = self.client.post(reverse("delete_list", args=[self.personal_list.id]), follow=True)

        self.assertRedirects(response, reverse("list_detail", args=[self.personal_list.id]))
        self.assertTrue(List.objects.filter(id=self.personal_list.id).exists())
        messages = list(response.context["messages"])
        self.assertTrue(any("You don't have permission to delete this list." in str(m) for m in messages))

    def test_owner_can_delete_personal_list(self):
        self.login(self.owner)

        response = self.client.post(reverse("delete_list", args=[self.personal_list.id]), follow=True)

        self.assertRedirects(response, reverse("profile", args=[self.owner.username]))
        self.assertFalse(List.objects.filter(id=self.personal_list.id).exists())
        messages = list(response.context["messages"])
        self.assertTrue(any("List deleted." in str(m) for m in messages))

    def test_club_owner_can_delete_club_list(self):
        self.login(self.club_owner)

        response = self.client.post(reverse("delete_list", args=[self.club_list.id]), follow=True)

        self.assertRedirects(response, reverse("profile", args=[self.club_owner.username]))
        self.assertFalse(List.objects.filter(id=self.club_list.id).exists())
        messages = list(response.context["messages"])
        self.assertTrue(any("List deleted." in str(m) for m in messages))