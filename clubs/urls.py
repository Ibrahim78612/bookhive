from django.urls import path
from . import views

urlpatterns = [

    path("", views.club_list, name="club_list"),

    path("<int:id>/", views.club_detail, name="club_detail"),

    path("<int:id>/join/", views.join_club, name="join_club"),

    path("<int:id>/leave/", views.leave_club, name="leave_club"),

]