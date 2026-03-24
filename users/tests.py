from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from books.models import Book
from clubs.models import Club
from lists.models import List
from reviews.models import Favourite, Review
from users.models import FriendRequest


class UserViewsBaseTestCase(TestCase):
    def setUp(self):
        self.password = "strong-pass-123"
        self.owner = User.objects.create_user(username="owner", password=self.password)
        self.other = User.objects.create_user(username="other", password=self.password)
        self.third = User.objects.create_user(username="third", password=self.password)

        self.book = Book.objects.create(
            hardcover_id="OL1W",
            title="The Testing Book",
            author="A. Author",
            year=2024,
        )

        self.club = Club.objects.create(
            name="Readers",
            description="Club desc",
            owner=self.owner,
        )
        self.club.members.add(self.owner, self.other)

        self.personal_list = List.objects.create(
            user=self.owner,
            name="Owner Personal List",
            description="Personal books",
        )
        self.club_list = List.objects.create(
            user=self.owner,
            club=self.club,
            name="Club List",
            description="Club books",
        )
        self.personal_list.books.add(self.book)
        self.club_list.books.add(self.book)

        Favourite.objects.create(user=self.owner, book=self.book)
        Review.objects.create(
            reviewer=self.owner,
            book=self.book,
            rating=5,
            comment="Excellent",
        )

    def login(self, user):
        self.client.force_login(user)


class MyProfileViewTests(UserViewsBaseTestCase):
    def test_my_profile_redirects_logged_out_user_to_login(self):
        response = self.client.get(reverse("my_profile"))

        self.assertRedirects(
            response,
            reverse("login"),
            fetch_redirect_response=False,
        )

    def test_my_profile_redirects_logged_in_user_to_own_profile(self):
        self.login(self.owner)

        response = self.client.get(reverse("my_profile"))

        self.assertRedirects(response, reverse("profile", args=[self.owner.username]))


class ProfileViewTests(UserViewsBaseTestCase):
    def test_profile_view_for_logged_out_user_shows_public_profile_without_friend_controls(self):
        response = self.client.get(reverse("profile", args=[self.owner.username]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/profile.html")
        self.assertEqual(response.context["profile_user"], self.owner)
        self.assertFalse(response.context["is_owner"])
        self.assertIsNone(response.context["friend_status"])
        self.assertContains(response, self.owner.username)
        self.assertNotContains(response, "Add Friend")
        self.assertNotContains(response, "Request Sent")
        self.assertNotContains(response, "Friends")
        self.assertEqual(
            list(response.context["personal_lists"].order_by("id")),
            list(List.objects.filter(user=self.owner, club__isnull=True).order_by("id")),
        )
        self.assertEqual(
            list(response.context["club_lists"].order_by("id")),
            list(List.objects.filter(club__members=self.owner).order_by("id")),
        )
        self.assertEqual(
            list(response.context["favourites"].order_by("id")),
            list(Favourite.objects.filter(user=self.owner).order_by("id")),
        )
        self.assertEqual(
            list(response.context["reviews"].order_by("id")),
            list(Review.objects.filter(reviewer=self.owner).order_by("id")),
        )

    def test_profile_view_for_owner_sets_is_owner_and_hides_friend_status(self):
        self.login(self.owner)

        response = self.client.get(reverse("profile", args=[self.owner.username]))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["is_owner"])
        self.assertIsNone(response.context["friend_status"])

        self.assertContains(response, self.owner.username)
        self.assertContains(response, "Readers")       
        self.assertContains(response, "The Testing Book")  
        self.assertContains(response, "Excellent")         

        self.assertNotContains(response, "Add Friend")

    def test_profile_view_for_other_logged_in_user_sets_friend_status_none_when_no_relationship(self):
        self.login(self.third)

        response = self.client.get(reverse("profile", args=[self.owner.username]))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["is_owner"])
        self.assertEqual(response.context["friend_status"], "none")
        self.assertContains(response, "Add Friend")

    def test_profile_view_shows_pending_friend_status(self):
        FriendRequest.objects.create(
            from_user=self.other,
            to_user=self.owner,
            status="pending",
        )
        self.login(self.other)

        response = self.client.get(reverse("profile", args=[self.owner.username]))

        self.assertEqual(response.context["friend_status"], "pending")
        self.assertContains(response, "Request Sent")

    def test_profile_view_shows_accepted_friend_status(self):
        FriendRequest.objects.create(
            from_user=self.other,
            to_user=self.owner,
            status="accepted",
        )
        self.login(self.other)

        response = self.client.get(reverse("profile", args=[self.owner.username]))

        self.assertEqual(response.context["friend_status"], "accepted")
        self.assertContains(response, "Friends")

    def test_profile_view_returns_404_for_unknown_username(self):
        response = self.client.get(reverse("profile", args=["missing-user"]))

        self.assertEqual(response.status_code, 404)


class FriendRequestActionTests(UserViewsBaseTestCase):
    def test_send_friend_request_redirects_logged_out_user_to_login(self):
        response = self.client.get(reverse("add_friend", args=[self.owner.username]))

        self.assertRedirects(response, reverse("login"), fetch_redirect_response=False)
        self.assertFalse(FriendRequest.objects.exists())

    def test_send_friend_request_creates_pending_request(self):
        self.login(self.other)

        response = self.client.get(reverse("add_friend", args=[self.owner.username]))

        self.assertRedirects(response, reverse("profile", args=[self.owner.username]))
        self.assertTrue(
            FriendRequest.objects.filter(
                from_user=self.other,
                to_user=self.owner,
                status="pending",
            ).exists()
        )

    def test_send_friend_request_to_self_does_nothing(self):
        self.login(self.owner)

        response = self.client.get(reverse("add_friend", args=[self.owner.username]))

        self.assertRedirects(response, reverse("profile", args=[self.owner.username]))
        self.assertFalse(FriendRequest.objects.exists())

    def test_send_friend_request_deletes_existing_pending_request_instead_of_creating_duplicate(self):
        FriendRequest.objects.create(
            from_user=self.other,
            to_user=self.owner,
            status="pending",
        )
        self.login(self.other)

        response = self.client.get(reverse("add_friend", args=[self.owner.username]))

        self.assertRedirects(response, reverse("profile", args=[self.owner.username]))
        self.assertFalse(FriendRequest.objects.exists())

    def test_send_friend_request_deletes_existing_declined_request(self):
        FriendRequest.objects.create(
            from_user=self.owner,
            to_user=self.other,
            status="declined",
        )
        self.login(self.other)

        response = self.client.get(reverse("add_friend", args=[self.owner.username]))

        self.assertRedirects(response, reverse("profile", args=[self.owner.username]))
        self.assertFalse(FriendRequest.objects.exists())

    def test_send_friend_request_keeps_existing_accepted_friendship(self):
        FriendRequest.objects.create(
            from_user=self.owner,
            to_user=self.other,
            status="accepted",
        )
        self.login(self.other)

        response = self.client.get(reverse("add_friend", args=[self.owner.username]))

        self.assertRedirects(response, reverse("profile", args=[self.owner.username]))
        self.assertEqual(FriendRequest.objects.count(), 1)
        self.assertEqual(FriendRequest.objects.get().status, "accepted")

    def test_accept_friend_request_redirects_logged_out_user_to_login(self):
        friend_request = FriendRequest.objects.create(
            from_user=self.other,
            to_user=self.owner,
            status="pending",
        )

        response = self.client.get(reverse("accept_friend_request", args=[friend_request.id]))

        self.assertRedirects(response, reverse("login"), fetch_redirect_response=False)
        friend_request.refresh_from_db()
        self.assertEqual(friend_request.status, "pending")

    def test_accept_friend_request_marks_request_accepted_for_recipient(self):
        friend_request = FriendRequest.objects.create(
            from_user=self.other,
            to_user=self.owner,
            status="pending",
        )
        self.login(self.owner)

        response = self.client.post(reverse("accept_friend_request", args=[friend_request.id]))

        self.assertRedirects(response, reverse("friends"))
        friend_request.refresh_from_db()
        self.assertEqual(friend_request.status, "accepted")

    def test_accept_friend_request_returns_404_for_wrong_user(self):
        friend_request = FriendRequest.objects.create(
            from_user=self.other,
            to_user=self.owner,
            status="pending",
        )
        self.login(self.third)

        response = self.client.post(reverse("accept_friend_request", args=[friend_request.id]))

        self.assertEqual(response.status_code, 404)
        friend_request.refresh_from_db()
        self.assertEqual(friend_request.status, "pending")

    def test_accept_friend_request_returns_404_for_non_pending_request(self):
        friend_request = FriendRequest.objects.create(
            from_user=self.other,
            to_user=self.owner,
            status="declined",
        )
        self.login(self.owner)

        response = self.client.post(reverse("accept_friend_request", args=[friend_request.id]))

        self.assertEqual(response.status_code, 404)
        friend_request.refresh_from_db()
        self.assertEqual(friend_request.status, "declined")

    def test_decline_friend_request_redirects_logged_out_user_to_login(self):
        friend_request = FriendRequest.objects.create(
            from_user=self.other,
            to_user=self.owner,
            status="pending",
        )

        response = self.client.get(reverse("decline_friend_request", args=[friend_request.id]))

        self.assertRedirects(response, reverse("login"), fetch_redirect_response=False)
        friend_request.refresh_from_db()
        self.assertEqual(friend_request.status, "pending")

    def test_decline_friend_request_marks_request_declined_for_recipient(self):
        friend_request = FriendRequest.objects.create(
            from_user=self.other,
            to_user=self.owner,
            status="pending",
        )
        self.login(self.owner)

        response = self.client.post(reverse("decline_friend_request", args=[friend_request.id]))

        self.assertRedirects(response, reverse("friends"))
        friend_request.refresh_from_db()
        self.assertEqual(friend_request.status, "declined")

    def test_decline_friend_request_returns_404_for_wrong_user(self):
        friend_request = FriendRequest.objects.create(
            from_user=self.other,
            to_user=self.owner,
            status="pending",
        )
        self.login(self.third)

        response = self.client.post(reverse("decline_friend_request", args=[friend_request.id]))

        self.assertEqual(response.status_code, 404)
        friend_request.refresh_from_db()
        self.assertEqual(friend_request.status, "pending")

    def test_unfriend_redirects_logged_out_user_to_login(self):
        friendship = FriendRequest.objects.create(
            from_user=self.owner,
            to_user=self.other,
            status="accepted",
        )

        response = self.client.get(reverse("unfriend", args=[self.other.username]))

        self.assertRedirects(response, reverse("login"), fetch_redirect_response=False)
        self.assertTrue(FriendRequest.objects.filter(id=friendship.id).exists())

    def test_unfriend_deletes_existing_accepted_friendship(self):
        FriendRequest.objects.create(
            from_user=self.owner,
            to_user=self.other,
            status="accepted",
        )
        self.login(self.owner)

        response = self.client.post(reverse("unfriend", args=[self.other.username]))

        self.assertRedirects(response, reverse("friends"))
        self.assertFalse(FriendRequest.objects.exists())

    def test_unfriend_does_nothing_if_no_accepted_friendship_exists(self):
        FriendRequest.objects.create(
            from_user=self.owner,
            to_user=self.other,
            status="pending",
        )
        self.login(self.owner)

        response = self.client.post(reverse("unfriend", args=[self.other.username]))

        self.assertRedirects(response, reverse("friends"))
        self.assertEqual(FriendRequest.objects.count(), 1)
        self.assertEqual(FriendRequest.objects.get().status, "pending")


class FriendsViewTests(UserViewsBaseTestCase):
    def test_friends_view_redirects_logged_out_user_to_login(self):
        response = self.client.get(reverse("friends"))

        self.assertRedirects(response, reverse("login"), fetch_redirect_response=False)

    def test_friends_view_shows_friends_received_pending_and_sent_pending(self):
        FriendRequest.objects.create(
            from_user=self.owner,
            to_user=self.other,
            status="accepted",
        )
        FriendRequest.objects.create(
            from_user=self.third,
            to_user=self.owner,
            status="pending",
        )
        sent_pending = FriendRequest.objects.create(
            from_user=self.owner,
            to_user=User.objects.create_user(username="fourth", password=self.password),
            status="pending",
        )

        self.login(self.owner)
        response = self.client.get(reverse("friends"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/friends.html")

        self.assertCountEqual(response.context["friends"], [self.other])
        self.assertEqual(
            list(response.context["received_pending"]),
            list(FriendRequest.objects.filter(id=FriendRequest.objects.get(from_user=self.third, to_user=self.owner).id)),
        )
        self.assertEqual(
            list(response.context["sent_pending"]),
            list(FriendRequest.objects.filter(id=sent_pending.id)),
        )

        self.assertContains(response, self.other.username)
        self.assertContains(response, self.third.username)
        self.assertContains(response, "Friend Requests")
        self.assertContains(response, "Sent Requests")
        

    def test_friends_view_handles_no_relationships(self):
        self.login(self.owner)

        response = self.client.get(reverse("friends"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No pending requests.")
        self.assertContains(response, "No friends yet.")