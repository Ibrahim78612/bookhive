from django.urls import path
from . import views

urlpatterns = [
    path("signup/", views.signup_view, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.my_profile, name="my_profile"),
    path("profile/<str:username>/", views.profile_view, name="profile"),
    path("send_friend_request/<str:username>/", views.send_friend_request, name="send_friend_request"),
    path("accept_friend_request/<int:request_id>/", views.accept_friend_request, name="accept_friend_request"),
    path("decline_friend_request/<int:request_id>/", views.decline_friend_request, name="decline_friend_request"),
    path("unfriend/<str:username>/", views.unfriend, name="unfriend"),
    path("friends/", views.friends_view, name="friends"),
]