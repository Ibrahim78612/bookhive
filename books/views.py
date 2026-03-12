from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Book
from reviews.models import Favourite, Review

from olapi.main import fetch_from_workid, cover_from_workid

def book_list(request):
    books = Book.objects.all()
    return render(request, "books/book_list.html", {"books": books})

def book_view(request, work_id):
    try:
        book_data = fetch_from_workid(work_id)
        book_cover = cover_from_workid(work_id, is_thumbnail=False)
        book_data["cover"] = book_cover
        book_data["work_id"] = work_id


        # Check if book is in user's favourites
        if request.user.is_authenticated:
            try:
                book_obj = Book.objects.get(hardcover_id=work_id)
                is_favourite = Favourite.objects.filter(user=request.user, book=book_obj).exists()
                favourite_count = Favourite.objects.filter(user=request.user).count()
            except Book.DoesNotExist:
                is_favourite = False
                favourite_count = Favourite.objects.filter(user=request.user).count()
            book_data["is_favourite"] = is_favourite
            book_data["favourite_count"] = favourite_count
            book_data["favourite_limit"] = 5
            try:
                book_data["reviews"] = Review.objects.filter(book=book_obj)
            except Review.DoesNotExist:
                book_data["reviews"] = None
    # TODO: make this redirect to specific error pages
    except Exception as e:
        print(f"couldn't retrieve, {e}")
        return redirect('/')
    return render(request, "books/book_view.html", context=book_data)

@login_required
def add_to_favourites(request, work_id):
    if request.method == 'POST':
        try:
            # Fetch book info from Open Library to create/get Book object
            book_data = fetch_from_workid(work_id)
            # Get or create book in database
            book, created = Book.objects.get_or_create(
                hardcover_id=work_id,
                defaults={
                    'title': book_data.get('title', 'Unknown'),
                    'author': ', '.join(book_data.get('authors', [])),
                }
            )
            
            # Check if already in favourites
            favourite = Favourite.objects.filter(user=request.user, book=book).first()
            
            if favourite:
                # Remove from favourites if already there
                favourite.delete()
            else:
                # Add to favourites if not at limit
                favourite_count = Favourite.objects.filter(user=request.user).count()
                if favourite_count < 5:
                    Favourite.objects.create(user=request.user, book=book)
            
            return redirect('book_view', work_id=work_id)
        except Exception as e:
            print(f"couldn't modify favourites, {e}")
            return redirect('book_view', work_id=work_id)
    return redirect('book_view', work_id=work_id)
