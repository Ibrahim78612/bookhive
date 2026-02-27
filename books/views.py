from django.shortcuts import render, redirect
from .models import Book

from olapi.main import fetch_from_workid, cover_from_workid

def book_list(request):
    books = Book.objects.all()
    return render(request, "books/book_list.html", {"books": books})

def book_view(request, work_id):
    try:
        print(f"fetching book data for {work_id}...")
        book_data = fetch_from_workid(work_id)
        print(f"fetching cover data for {work_id}...")
        book_cover = cover_from_workid(work_id, is_thumbnail=False)
        print(book_data, book_cover)
        book_data["cover"] = book_cover
    # TODO: make this redirect to specific error pages
    except Exception as e:
        print(f"couldn't retrieve, {e}")
        return redirect('/')
    return render(request, "books/book_view.html", context=book_data)
