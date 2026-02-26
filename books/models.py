from django.db import models

class Book(models.Model):
    hardcover_id = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    year = models.IntegerField(null=True, blank=True)
    genre = models.CharField(max_length=100, blank=True)
    cover_image = models.URLField(blank=True)

    def __str__(self):
        return self.title