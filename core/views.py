from django.shortcuts import render, redirect
from django.http import JsonResponse
from olapi.main import fetch_with_title
from core.search_converter import fetch_title_to_search

def index(request):
    return render(request, "index.html")

def search(request):
    query = request.GET.get('query', '')
    # default search type
    search_type = request.GET.get('type', 'books')
    if query == '':
        return redirect("/")

    data = None
    if search_type == 'books':
        data = fetch_title_to_search(fetch_with_title(query))
        print(data)
    # if search_type == 'users':
    # data = Users.objects.search(query)

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
