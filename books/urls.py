from django.urls import path
from . import views

urlpatterns = [
        path("<slug:work_id>/", views.book_view, name="book_view")
        ]
