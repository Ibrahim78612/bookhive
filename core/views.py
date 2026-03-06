from django.shortcuts import render, redirect
from olapi.main import fetch_with_title

def index(request):
    return render(request, "index.html")

def search(request):
    query = request.GET.get('query', '')
    print(query)
    if query == '':
        print("none moment")
        return redirect("/")
    books_data = fetch_with_title(query)
    context = {
            "docs": books_data,
            }
    print(books_data)
    return render(request, "search.html", context=context)
