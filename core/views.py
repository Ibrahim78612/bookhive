from django.shortcuts import render, redirect
from django.http import JsonResponse
from olapi.main import fetch_with_title

def index(request):
    return render(request, "index.html")

def search(request):
    query = request.GET.get('query', '')
    if query == '':
        return redirect("/")
    books_data = fetch_with_title(query)
    context = {
        "docs": books_data,
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
