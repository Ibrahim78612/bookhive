from django.urls import path
from . import views

urlpatterns = [
    path("", views.club_list, name="club_list"),
    path("add/", views.club_create, name="club_create"), 
    path("<int:id>/", views.club_detail, name="club_detail"),
    path("<int:id>/edit/", views.club_edit, name="club_edit"), 
    path("<int:id>/join/", views.join_club, name="join_club"),
    path("<int:id>/leave/", views.leave_club, name="leave_club"),
    path('<int:id>/delete/', views.club_delete, name='club_delete'),
]