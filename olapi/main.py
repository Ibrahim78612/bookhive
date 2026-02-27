from urllib.error import HTTPError
from olapi.ol_api_helpers import *

# convenient work id for purposes of testing
# points to Hacker's Delight. 
test_workid = "OL8022414W"
# This is a work id that is syntactically valid but doesn't point anywhere. Good for testing what happens if an invalid work id is entered somewhere. 
fake_workid = "OL111111111111111111W"

# this will cache book data so that we dont need to fetch from internet every time

@check_workid
def fetch_from_workid(work_id, raise_errors=True):
    """
    Takes in an OpenLibrary ID (of format OL8022414W) and returns title, author(s), date, subjects and description of the book. Passing in raise_errors = False will return None instead of propagating the error (likely will come in handy for lists)
    """
    fetch_url = f"https://openlibrary.org/works/{work_id}.json"
    try:
        book_data = json_from_url(fetch_url)
    except:
        if raise_errors == False: return None
        raise
    else:
        key_data = {
            "title": book_data.get("title", "Unknown"),
            "authors": fetch_authors(book_data.get("authors", None)),
            "description": book_data.get("description", "This book has no description."),
            "date": book_data.get("first_publish_date", "N/A"),
            "subjects": book_data.get("subjects", []),
        }
        return key_data

@check_workid
def cover_from_workid(work_id, is_thumbnail=True):
    """
    Takes in an OpenLibrary ID and returns the url to OpenLibrary's cover (which can then be used as your src in the img tag). Set is_thumbnail to true if the cover's display will be quite small (like in a list). If an error is encountered while fetching, will return None.
    """
    base = f"https://covers.openlibrary.org/b/olid/{work_id}"
    size = "M"
    if is_thumbnail: size = "S"

    check_exists_url = f"{base}.json"
    try:
        json_from_url(check_exists_url)
    except HTTPError as err:
        if err.code != 404:
            print(f"Non 404 error encountered when fetching cover for {work_id}: {err}")
        return None # pages expected to load unknown image if returns None
    else:
        cover_cache[work_id] = base
        return f"{base}-{size}.jpg"
    return img

# for now this is a helper function to help find book ids if you need test data for example
# will be expanded to help implement search later
@use_search_string
def fetch_with_title(title):
    """
    rough function to help with finding openlibrary ids during development
    will be refined later to help with adding search
    """
    title = normalise_string(title)
    fetch_url = "https://openlibrary.org/search.json?q="+title
    book_data = json_from_url(fetch_url)
    return book_data
