from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from .models import Club
from .forms import ClubForm


def club_list(request):
    if not request.user.is_authenticated:
        return render(request, "clubs/clubs.html", {
            "clubs": []
        })

    clubs = Club.objects.all()
    return render(request, "clubs/clubs.html", {
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


@login_required
def club_create(request):
    if request.method == "POST":
        form = ClubForm(request.POST)
        if form.is_valid():
            club = form.save(commit=False)
            club.owner = request.user
            club.save()
            club.members.add(request.user)
            return redirect("club_detail", id=club.id)
    else:
        form = ClubForm()

    return render(request, "clubs/club_form.html", {
        "form": form,
        "action": "Create"
    })


@login_required
def club_edit(request, id):
    club = get_object_or_404(Club, id=id)

    if club.owner != request.user:
        raise PermissionDenied

    if request.method == "POST":
        form = ClubForm(request.POST, instance=club)
        if form.is_valid():
            form.save()
            return redirect("club_detail", id=club.id)
    else:
        form = ClubForm(instance=club)

    return render(request, "clubs/club_form.html", {
        "form": form,
        "action": "Edit",
        "club": club
    })


@login_required
def club_delete(request, id):
    club = get_object_or_404(Club, id=id)
    if club.owner == request.user:
        club.delete()
    return redirect("club_list")


@login_required
def my_clubs(request):
    owned = Club.objects.filter(owner=request.user)
    joined = Club.objects.filter(members=request.user)

    return render(request, 'clubs/my_clubs.html', {
        'owned': owned,
        'joined': joined
    })