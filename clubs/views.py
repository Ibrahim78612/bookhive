from django.shortcuts import render
from .models import Club

def club_list(request):
    # This fetches all the clubs from the database
    clubs = Club.objects.all()
    # This sends the data to an HTML template (which we will need to create)
    return render(request, 'clubs/club_list.html', {'clubs': clubs})