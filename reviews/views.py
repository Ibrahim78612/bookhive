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

    existing_review = (
        Review.objects.filter(book=book, reviewer=request.user)
        .order_by("-created_at")
        .first()
    )
    show_review_form = (existing_review is None) or (
        request.GET.get("edit", "0") in {"1", "true", "yes", "on"}
    )

    if request.method == "POST":
        comment = request.POST.get("comment", "").strip()
        rating_raw = request.POST.get("rating", "").strip()

        try:
            rating = int(rating_raw)
        except (TypeError, ValueError):
            rating = existing_review.rating if existing_review else 3

        rating = max(1, min(5, rating))

        if comment:
            # If the user already reviewed this book, update their review instead
            # of creating duplicates. Update all matches to be resilient if the
            # database already contains duplicates from older behavior.
            user_reviews_qs = Review.objects.filter(book=book, reviewer=request.user)
            updated_count = user_reviews_qs.update(rating=rating, comment=comment)
            if updated_count == 0:
                Review.objects.create(
                    reviewer=request.user,
                    book=book,
                    rating=rating,
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
        "existing_review": existing_review,
        "show_review_form": show_review_form,
    }

    return render(request, "reviews/reviews.html", context)
