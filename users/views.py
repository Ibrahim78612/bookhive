from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from clubs.models import Club
from lists.models import List
from reviews.models import Favourite

def signup_view(request):
    form = UserCreationForm(request.POST or None)
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
    clubs = user.clubs.all()
    lists = List.objects.filter(user=user)
    favourites = Favourite.objects.filter(user=user).select_related('book')
    return render(request, "users/profile.html", {
        "user": user,
        "clubs": clubs,
        "lists": lists,
        "favourites": favourites,
    })