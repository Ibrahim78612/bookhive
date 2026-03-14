from django.db import models
from django.contrib.auth.models import User
from books.models import Book
from clubs.models import Club

class List(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lists')
    club = models.OneToOneField(Club, on_delete=models.CASCADE, null=True, blank=True, related_name='list')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    books = models.ManyToManyField(Book, related_name='lists', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def can_edit(self, user):
        if self.club:
            return self.club.owner == user
        return self.user == user
