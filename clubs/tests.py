from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Club

class ClubAppTests(TestCase):

    def setUp(self):
        self.owner_user = User.objects.create_user(username='owner', password='password123')
        self.other_user = User.objects.create_user(username='other', password='password123')

        self.club = Club.objects.create(
            name="Test Club",
            description="A club for testing purposes.",
            owner=self.owner_user
        )
        self.club.members.add(self.owner_user)

    def test_club_str_method(self):
        self.assertEqual(str(self.club), "Test Club")

    def test_club_list_unauthenticated(self):
        response = self.client.get(reverse('club_list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['clubs']), [])

    def test_club_list_authenticated(self):
        self.client.login(username='other', password='password123')
        response = self.client.get(reverse('club_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.club, response.context['clubs'])

    def test_club_detail_view(self):
        response = self.client.get(reverse('club_detail', args=[self.club.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['club'], self.club)

    def test_create_club(self):
        self.client.login(username='other', password='password123')
        
        response = self.client.post(reverse('club_create'), {
            'name': 'New Book Club',
            'description': 'We read books.'
        })
        
        new_club = Club.objects.get(name='New Book Club')
        self.assertRedirects(response, reverse('club_detail', args=[new_club.id]))
        
        self.assertEqual(new_club.owner, self.other_user)
        self.assertIn(self.other_user, new_club.members.all())

    def test_join_and_leave_club(self):
        self.client.login(username='other', password='password123')
        
        response = self.client.get(reverse('join_club', args=[self.club.id]))
        self.assertRedirects(response, reverse('club_detail', args=[self.club.id]))
        self.assertIn(self.other_user, self.club.members.all())
        
        response = self.client.get(reverse('leave_club', args=[self.club.id]))
        self.assertRedirects(response, reverse('club_detail', args=[self.club.id]))
        self.assertNotIn(self.other_user, self.club.members.all())

    def test_edit_club_as_owner(self):
        self.client.login(username='owner', password='password123')
        
        response = self.client.post(reverse('club_edit', args=[self.club.id]), {
            'name': 'Updated Test Club',
            'description': 'New description.'
        })
        
        self.assertRedirects(response, reverse('club_detail', args=[self.club.id]))
        self.club.refresh_from_db()
        self.assertEqual(self.club.name, 'Updated Test Club')

    def test_edit_club_as_non_owner(self):
        self.client.login(username='other', password='password123')
        
        response = self.client.post(reverse('club_edit', args=[self.club.id]), {
            'name': 'Hacked Club',
            'description': 'Trying to bypass rules.'
        })
        
        self.assertEqual(response.status_code, 403)
        self.club.refresh_from_db()
        self.assertEqual(self.club.name, 'Test Club')

    def test_my_clubs_view(self):
        self.client.login(username='owner', password='password123')
        
        response = self.client.get(reverse('my_clubs'))
        self.assertEqual(response.status_code, 200)
        
        self.assertIn(self.club, response.context['owned'])
        self.assertIn(self.club, response.context['joined'])