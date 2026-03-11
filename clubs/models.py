from django.db import models
from django.contrib.auth.models import User

class Club(models.Model):

    name = models.CharField(max_length=200)
    description = models.TextField()
    founded_date = models.DateField(auto_now_add=True)

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="owned_clubs",
        null=True,
        blank=True
    )

    members = models.ManyToManyField(
        User,
        related_name="clubs",
        blank=True
    )

    def __str__(self):
        return self.name