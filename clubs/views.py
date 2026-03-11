from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Club


def club_list(request):

    clubs = Club.objects.all()

    return render(request, "clubs/club_list.html", {
        "clubs": clubs
    })


def club_detail(request, id):

    club = get_object_or_404(Club, id=id)

    return render(request, "clubs/club_detail.html", {
        "club": club
    })


@login_required
def join_club(request, id):

    club = get_object_or_404(Club, id=id)

    club.members.add(request.user)

    return redirect("club_detail", id=id)


@login_required
def leave_club(request, id):

    club = get_object_or_404(Club, id=id)

    club.members.remove(request.user)

    return redirect("club_detail", id=id)