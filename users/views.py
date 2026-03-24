from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.db.models import Q
from django import forms

from reviews.models import Favourite, Review
from lists.models import List
from .models import FriendRequest


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

    if request.method == "POST":
        username_input = request.POST.get("username")
        password = request.POST.get("password")

        user = None

        if "@" in username_input:
            try:
                user_obj = User.objects.get(email=username_input)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None
        else:
            user = authenticate(request, username=username_input, password=password)

        if user is not None:
            login(request, user)
            return redirect("/")

    return render(request, "users/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("/")


def my_profile(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return redirect('profile', username=request.user.username)


def profile_view(request, username):
    profile_user = get_object_or_404(User, username=username)

    is_owner = request.user.is_authenticated and request.user == profile_user

    friend_status = None
    if request.user.is_authenticated and request.user != profile_user:
        req = FriendRequest.objects.filter(
            Q(from_user=request.user, to_user=profile_user) |
            Q(from_user=profile_user, to_user=request.user)
        ).first()

        if req:
            friend_status = req.status
        else:
            friend_status = 'none'

    favourites = Favourite.objects.filter(user=profile_user).select_related("book")
    clubs = profile_user.clubs.all()
    personal_lists = List.objects.filter(user=profile_user, club__isnull=True)
    club_lists = List.objects.filter(club__members=profile_user).select_related('club')
    reviews = Review.objects.filter(reviewer=profile_user).select_related('book')

    return render(request, "users/profile.html", {
        "profile_user": profile_user,
        "is_owner": is_owner,
        "friend_status": friend_status,
        "clubs": clubs,
        "personal_lists": personal_lists,
        "club_lists": club_lists,
        "favourites": favourites,
        "reviews": reviews,
    })


def send_friend_request(request, username):
    if not request.user.is_authenticated:
        return redirect('login')

    to_user = get_object_or_404(User, username=username)

    if request.user == to_user:
        return redirect('profile', username=username)

    existing = FriendRequest.objects.filter(
        Q(from_user=request.user, to_user=to_user) |
        Q(from_user=to_user, to_user=request.user)
    ).first()

    if existing:
        if existing.status != 'accepted':
            existing.delete()
    else:
        FriendRequest.objects.create(from_user=request.user, to_user=to_user, status='pending')

    return redirect('profile', username=username)


def accept_friend_request(request, request_id):
    if not request.user.is_authenticated:
        return redirect('login')

    friend_request = get_object_or_404(
        FriendRequest,
        id=request_id,
        to_user=request.user,
        status='pending'
    )

    friend_request.status = 'accepted'
    friend_request.save()

    return redirect('friends')


def decline_friend_request(request, request_id):
    if not request.user.is_authenticated:
        return redirect('login')

    friend_request = get_object_or_404(
        FriendRequest,
        id=request_id,
        to_user=request.user,
        status='pending'
    )

    friend_request.status = 'declined'
    friend_request.save()
    return redirect('friends')


def unfriend(request, username):
    if not request.user.is_authenticated:
        return redirect('login')

    friend = get_object_or_404(User, username=username)

    req = FriendRequest.objects.filter(
        Q(from_user=request.user, to_user=friend) |
        Q(from_user=friend, to_user=request.user),
        status='accepted'
    ).first()

    if req:
        req.delete()

    return redirect('friends')


def friends_view(request):
    if not request.user.is_authenticated:
        return redirect('login')

    friends_requests = FriendRequest.objects.filter(
        Q(from_user=request.user) | Q(to_user=request.user),
        status='accepted'
    )

    friends = []
    for req in friends_requests:
        if req.from_user == request.user:
            friends.append(req.to_user)
        else:
            friends.append(req.from_user)

    received_pending = FriendRequest.objects.filter(
        to_user=request.user,
        status='pending'
    )

    sent_pending = FriendRequest.objects.filter(
        from_user=request.user,
        status='pending'
    )

    return render(request, 'users/friends.html', {
        'friends': friends,
        'received_pending': received_pending,
        'sent_pending': sent_pending,
    })