from django.urls import path
from . import views

urlpatterns = [
    path("", views.book_list, name="book_list"),
    path("<slug:work_id>/", views.book_view, name="book_view"),
    path("<slug:work_id>/add-to-favourites/", views.add_to_favourites, name="add_to_favourites"),
]
