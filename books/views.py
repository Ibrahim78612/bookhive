from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Book
from lists.models import List
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
        book_data["reviews"] = None

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

            # Provide user's lists for the "Add to a List" action
            user_lists = List.objects.filter(
                Q(user=request.user) | Q(club__members=request.user)
            ).distinct()
            book_data["user_lists"] = user_lists

        try:
            book_obj = Book.objects.get(hardcover_id=work_id)
            book_data["reviews"] = Review.objects.filter(book=book_obj)
        except:
            pass # if book or reviews couldn't be fetched, this doesn't ultimately matter
    # TODO: make this redirect to specific error pages
    except Exception as e:
        print(f"couldn't retrieve, {e}")
        return redirect('/')
    return render(request, "books/book_view.html", context=book_data)

@login_required
def add_book_to_list(request, work_id):
    if request.method != 'POST':
        return redirect('book_view', work_id=work_id)

    list_id = request.POST.get('list_id')
    if not list_id:
        messages.error(request, "Please select a list.")
        return redirect('book_view', work_id=work_id)

    list_obj = get_object_or_404(List, id=list_id)
    if not list_obj.can_edit(request.user):
        messages.error(request, "You don't have permission to edit that list.")
        return redirect('book_view', work_id=work_id)

    # Ensure book exists in database
    try:
        book_obj = Book.objects.get(hardcover_id=work_id)
    except Book.DoesNotExist:
        try:
            book_data = fetch_from_workid(work_id)
            book_obj = Book.objects.create(
                hardcover_id=work_id,
                title=book_data.get('title', work_id),
                author=', '.join(book_data.get('authors', [])) if book_data.get('authors') else '',
            )
        except Exception:
            messages.error(request, "Could not find book information to add.")
            return redirect('book_view', work_id=work_id)

    if list_obj.books.filter(hardcover_id=work_id).exists():
        messages.info(request, "Book is already in the list.")
    else:
        list_obj.books.add(book_obj)
        messages.success(request, f"Added '{book_obj.title}' to {list_obj.name}.")

    return redirect('list_detail', list_id=list_obj.id)

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
