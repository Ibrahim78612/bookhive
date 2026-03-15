from reviews.models import Review
from lists.models import List
from clubs.models import Club

def fetch_title_to_search(fetch_data):
    """
    Converts the sort of data you get from fetch_from_title into data useable by the search page.
    """
    new_list = []
    for item in fetch_data:
        if item["first_publish_date"] == None:
            item["first_publish_date"] = "-"
        if item["authors"] == None:
            item["authors"] = []

        item = {
                "image": item["cover"],
                "title": item["title"],
                "id": item["workid"],
                "meta": [item["first_publish_date"], ", ".join(item["authors"])],
                }
        new_list.append(item)
    return new_list

def user_data_to_search(user_queryset):
    """
    Converts user model data to data useable by the search page.
    """
    new_list = []
    for user in user_queryset:
        print(user)
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
