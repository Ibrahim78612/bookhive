from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import List
from books.models import Book
from clubs.models import Club

def list_detail(request, list_id):
    list_obj = get_object_or_404(List, id=list_id)
    can_edit = request.user.is_authenticated and list_obj.can_edit(request.user)

    # Allow viewing if user created it, or if it's a club list and user is member (or anonymous)
    if not (list_obj.user == request.user or (list_obj.club and request.user in list_obj.club.members.all()) or not request.user.is_authenticated):
        # For anonymous, allow viewing public lists? But since no public/private, allow all for now
        pass  # Allow viewing

    if request.method == 'POST' and can_edit:
        if 'add_book' in request.POST:
            book_id = request.POST.get('book_id')
            if book_id:
                try:
                    book = Book.objects.get(hardcover_id=book_id)
                    if not list_obj.books.filter(hardcover_id=book_id).exists():
                        list_obj.books.add(book)
                        messages.success(request, f"Added {book.title} to the list.")
                    else:
                        messages.info(request, "Book is already in the list.")
                except Book.DoesNotExist:
                    messages.error(request, "Book not found.")
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
