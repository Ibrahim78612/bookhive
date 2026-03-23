from django.shortcuts import render, redirect
from django.http import JsonResponse

# model import for search types
from django.contrib.auth.models import User
from clubs.models import Club
from lists.models import List


from olapi.main import fetch_with_title
from core.search_converter import *

def index(request):
    return render(request, "index.html")

def search(request):
    query = request.GET.get('query', '')
    # default search type
    search_type = request.GET.get('type', '')
    allowed_search_types = ['book_view', 'profile', 'list_detail', 'club_detail']

    if query == '' or search_type not in allowed_search_types:
        return redirect("/")

    data = None
    if search_type == 'book_view':
        data = fetch_title_to_search(fetch_with_title(query))
    if search_type == 'profile':
        data = user_data_to_search(User.objects.filter(username__contains=query))
    if search_type == 'list_detail':
        data = list_data_to_search(List.objects.filter(name__contains=query))
    if search_type == 'club_detail':
        data = club_data_to_search(Club.objects.filter(name__contains=query))

    context = {
        "query": query,
        "to_page": search_type,
        "docs": data,
    }

    return render(request, "search.html", context=context)

def clubs(request):
    return render(request, "clubs/clubs.html")

def search_json(request):
    query = request.GET.get('query', '')
    if query == '':
        return JsonResponse({})
    books_data = {"books": fetch_with_title(query)}
    return JsonResponse(books_data)
