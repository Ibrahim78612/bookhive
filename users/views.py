from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from reviews.models import Favourite
from lists.models import List
from django import forms

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")


def signup_view(request):
    form = SignUpForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("/")

    return render(request, "users/signup.html", {"form": form})


def login_view(request):
    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect("/")

    return render(request, "users/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("/")


def profile_view(request):

    user = request.user

    favourites = Favourite.objects.filter(user=user).select_related("book")

    clubs = user.clubs.all()

    # Get personal lists
    personal_lists = List.objects.filter(user=user, club__isnull=True)

    # Get club lists for clubs user is member of
    club_lists = List.objects.filter(club__members=user).select_related('club')

    return render(request, "users/profile.html", {
        "user": user,
        "clubs": clubs,
        "personal_lists": personal_lists,
        "club_lists": club_lists,
        "favourites": favourites,
    })