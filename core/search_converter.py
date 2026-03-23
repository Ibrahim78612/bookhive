from reviews.models import Review
from lists.models import List
from clubs.models import Club
from books.models import Book

def fetch_title_to_search(fetch_data, order_by):
    """
    Converts the sort of data you get from fetch_from_title into data useable by the search page.
    """
    new_list = []
    rev = True

    ordering = order_by.split("_")[0]
    if order_by.split("_")[-1] == "desc":
        rev = False

    for item in fetch_data:
        if item["first_publish_date"] == None:
            item["first_publish_date"] = "-"
        if item["authors"] == None:
            item["authors"] = []

        this_book = Book.objects.filter(hardcover_id=item["workid"]).first()
        rating = 0
        review_count = 0
        rating_str = "No reviews."

        # there is definetly a better way to do this code
        if this_book != None:
            reviews = Review.objects.filter(book=this_book)
            review_count = reviews.count()
            if review_count != 0:
                rating = sum([review.rating for review in reviews]) / review_count
                rating_str = f"{rating:.1f} "+ ("⭐" * int(rating))

        item = {
                "image": item["cover"],
                "title": item["title"],
                "id": item["workid"],
                "meta": [rating_str, item["first_publish_date"], ", ".join(item["authors"])],
                "review": rating,
                "reviewcount": review_count
                }
        new_list.append(item)

    new_list.sort(key=lambda x: x[ordering], reverse=rev)
    return (new_list, ["review", "reviewcount"])

def user_data_to_search(user_queryset):
    """
    Converts user model data to data useable by the search page.
    """
    new_list = []
    for user in user_queryset:
        # get the user's metadata
        clubs = user.clubs.all().count()
        reviews = Review.objects.filter(reviewer=user).count()
        lists = List.objects.filter(user=user, club__isnull=True).count()
        joined = user.date_joined.date()

        item = {
                "image": None, # users currently have no profile pictures, so let the search template use a default image
                "title": user.username,
                "id": user.username,
                "meta": [f"Registered: {joined}", f"Reviews: {reviews}", f"Lists: {lists}", f"Clubs: {clubs}"]
                }
        new_list.append(item)
    return new_list

def club_data_to_search(club_queryset):
    """
    Converts club model data to data useable by the search page.
    """
    new_list = []
    for club in club_queryset:
        # get some relevant list metadata
        name = club.name
        owner_name = club.owner.username
        member_count = club.members.all().count()

        item = {
                "image": None,
                "title": name,
                "id": club.id,
                "meta": [f"👑 {owner_name}", f"👤 {member_count}"]
                }
        new_list.append(item)
    return new_list

def list_data_to_search(list_queryset):
    """
    Converts list model data to data useable by the search page.
    """
    new_list = []
    for book_list in list_queryset:
        name = book_list.name
        book_count = book_list.books.all().count()
        user = book_list.user.username

        item = {
                "image": None,
                "title": name,
                "id": book_list.id,
                "meta": [f"Created by {user}", f"Has {book_count} books"]
                }
        new_list.append(item)
    return new_list
