from django.db import models

class Club(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    founded_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.name