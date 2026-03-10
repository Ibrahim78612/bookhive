from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from books.models import Book
from .models import Review
from olapi.main import fetch_from_workid, cover_from_workid


@login_required
def book_reviews(request, work_id):
    """
    Display all reviews for a book and allow the user to add a new review.
    """
    try:
        book_data = fetch_from_workid(work_id)
        cover_url = cover_from_workid(work_id, is_thumbnail=False)
    except Exception:
        return redirect("index")

    book, _ = Book.objects.get_or_create(
        hardcover_id=work_id,
        defaults={
            "title": book_data.get("title", "Unknown"),
            "author": ", ".join(book_data.get("authors", [])),
        },
    )

    if request.method == "POST":
        comment = request.POST.get("comment", "").strip()

        if comment:
            Review.objects.create(
                reviewer=request.user,
                book=book,
                rating=5,
                comment=comment,
            )
            return redirect("book_reviews", work_id=work_id)

    reviews = Review.objects.filter(book=book).select_related("reviewer").order_by(
        "-created_at"
    )

    context = {
        "work_id": work_id,
        "book": book,
        "cover": cover_url,
        "title": book_data.get("title", ""),
        "authors": book_data.get("authors", []),
        "first_publish_date": book_data.get("first_publish_date", ""),
        "subjects": book_data.get("subjects", []),
        "reviews": reviews,
    }

    return render(request, "reviews/reviews.html", context)

