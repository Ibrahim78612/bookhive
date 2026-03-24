import os
import random

import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bookhive.settings")
django.setup()

# import all of the models
from books.models import Book
from clubs.models import Club
from lists.models import List
from reviews.models import Review
from django.contrib.auth.models import User
from olapi.main import fetch_from_workid

def populate():
    # Ensure population script's behaviour is consistent between runs.
    random.seed(0)

    user_count = 50
    club_count = 25
    list_count = 100
    review_count = 500

    # the books are taken from the search page
    with open("sample_data/books/books.csv") as f:
        books = [line.strip() for line in f]
        for work_id in books:
            book_data = fetch_from_workid(work_id)
            print(f"fetched {book_data['title']}")
            Book.objects.get_or_create(
                    hardcover_id=work_id,
                    defaults = {
                        "title": book_data.get("title", "Unknown"),
                        "author": ", ".join(book_data.get("authors", [])),
                        }
                    )


    with open("sample_data/oxford3000/oxford3000.csv") as f:
        word_list = [line.split(",")[0].replace(" ", "").title() for line in f]


    with open("sample_data/starters/starters.csv") as f:
        starters = [line.strip() for line in f]
    with open("sample_data/adjectives/adjectives.csv") as f:
        adjs = [line.strip() for line in f]

    word_sample = random.sample(word_list, 2*user_count)
    users = [f"{x}{y}" for x, y in zip(word_sample[:-1:2], word_sample[1::2])]

    for user in users: add_user(user)

    for i in range(review_count): 
        add_review(
                f"{random.choice(starters)} {random.choice(adjs)}",
                random.randint(1,5),
                random.choice(users),
                random.choice(books)
                )

    for i in range(list_count):
        add_list(
                f"{random.choice(word_list)} List",
                f"{random.choice(adjs)} {random.choice(word_list)} books",
                random.choice(users),
                random.sample(books, random.randint(1,10))
                )

    for i in range(club_count):
        add_club(
                f"{random.choice(word_list)} club",
                f"A club for {random.choice(adjs)} readers.",
                random.sample(users, random.randint(1,10))
                )


def add_user(name):
    try:
        usr = User.objects.create_user(name, f"{name}@email.com", "password")
        print(f"created user {name}")
        usr.save()
    except:
        usr = User.objects.get(username=name)
    return usr

def add_review(comment, rating, username, book_id):
    book = Book.objects.get_or_create(hardcover_id=book_id)[0]
    reviewer = User.objects.get_or_create(username=username)[0]
    rev = Review.objects.get_or_create(comment=comment, rating=rating, reviewer=reviewer, book=book)[0]
    rev.save()
    return rev

# first user in user_list is the owner
def add_club(name, desc, user_list):
    owner = User.objects.get_or_create(username=user_list[0])[0]
    club = Club.objects.get_or_create(name=name, owner=owner)[0]
    club.members.add(*User.objects.filter(username__in=user_list[1:]))
    club.description = desc
    club.save()
    return club

def add_list(name, desc, creator, book_list):
    user = User.objects.get_or_create(username=creator)[0]
    listed = List.objects.get_or_create(name=name, user=user)[0]
    listed.description = desc
    listed.books.add(*Book.objects.filter(hardcover_id__in=book_list))

if __name__ == "__main__":
    print("Starting BookHive population script..")
    populate()
