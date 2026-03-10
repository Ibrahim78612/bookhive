from django.urls import path
from . import views

urlpatterns = [
    path("reviews/<slug:work_id>/", views.book_reviews, name="book_reviews"),
]

