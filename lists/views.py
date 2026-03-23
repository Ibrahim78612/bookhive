from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import List
from books.models import Book
from clubs.models import Club
from olapi.main import fetch_from_workid, cover_from_workid


def list_detail(request, list_id):
    list_obj = get_object_or_404(List, id=list_id)
    can_edit = request.user.is_authenticated and list_obj.can_edit(request.user)

    # Allow viewing for everyone (public by default)
    # Editing only for list owner (or club owner for club lists)

    if request.method == 'POST' and can_edit:
        if 'add_book' in request.POST:
            book_id = request.POST.get('book_id')

            if book_id:
                try:
                    # First try to find the book in the local database
                    book = Book.objects.get(hardcover_id=book_id)

                except Book.DoesNotExist:
                    # If the book is not stored locally yet,
                    # fetch it from OpenLibrary and create it
                    try:
                        book_data = fetch_from_workid(book_id)
                        book = Book.objects.create(
                            hardcover_id=book_id,
                            title=book_data.get('title', book_id),
                            author=', '.join(book_data.get('authors', [])) if book_data.get('authors') else '',
                            year=book_data.get('first_publish_date'),
                            cover_image=cover_from_workid(book_id, is_thumbnail=True) or '',
                        )
                    except Exception:
                        messages.error(request, "Could not fetch that book from OpenLibrary.")
                        return redirect('list_detail', list_id=list_id)

                if not list_obj.books.filter(hardcover_id=book_id).exists():
                    list_obj.books.add(book)
                    messages.success(request, f"Added {book.title} to the list.")
                else:
                    messages.info(request, "Book is already in the list.")

        elif 'remove_book' in request.POST:
            book_id = request.POST.get('remove_book_id')
            if book_id:
                try:
                    book = list_obj.books.get(hardcover_id=book_id)
                    list_obj.books.remove(book)
                    messages.success(request, f"Removed {book.title} from the list.")
                except Book.DoesNotExist:
                    messages.error(request, "Book not in list.")

    return render(request, 'lists/list_detail.html', {
        'list': list_obj,
        'can_edit': can_edit,
    })


@login_required
def edit_list(request, list_id):
    list_obj = get_object_or_404(List, id=list_id)

    if not list_obj.can_edit(request.user):
        messages.error(request, "You don't have permission to edit this list.")
        return redirect('list_detail', list_id=list_id)

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        if not name:
            messages.error(request, "List name is required.")
        else:
            list_obj.name = name
            list_obj.description = description
            list_obj.save()
            messages.success(request, "List updated.")
            return redirect('list_detail', list_id=list_id)

    return render(request, 'lists/edit_list.html', {
        'list': list_obj,
    })


@login_required
def delete_list(request, list_id):
    list_obj = get_object_or_404(List, id=list_id)

    if not list_obj.can_edit(request.user):
        messages.error(request, "You don't have permission to delete this list.")
        return redirect('list_detail', list_id=list_id)

    if request.method == 'POST':
        list_obj.delete()
        messages.success(request, "List deleted.")
        return redirect('profile')

    return render(request, 'lists/delete_list.html', {
        'list': list_obj,
    })


@login_required
def create_list(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        if name:
            list_obj = List.objects.create(user=request.user, name=name, description=description)
            messages.success(request, f"Created list '{name}'.")
            return redirect('list_detail', list_id=list_obj.id)
        else:
            messages.error(request, "List name is required.")
    return render(request, 'lists/create_list.html')