from urllib.error import HTTPError
from olapi.ol_api_helpers import *
#from ol_api_helpers import *

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
        book_data = json_from_url(fetch_url, processing_func=strip_book_data)
    except:
        if raise_errors == False: return None
        raise
    return book_data

@check_workid
def cover_from_workid(work_id, is_thumbnail=True):
    """
    Takes in an OpenLibrary ID and returns the url to OpenLibrary's cover (which can then be used as your src in the img tag). Set is_thumbnail to true if the cover's display will be quite small (like in a list). If an error is encountered while fetching, will return None.
    """
    book_data = fetch_from_workid(work_id, True)

    if book_data == None or book_data["covers"] == None:
        return None

    base = f"https://covers.openlibrary.org/b/id/{book_data['covers']}"
    size = "L"
    if is_thumbnail: size = "M"

    return f"{base}-{size}.jpg"

# for now this is a helper function to help find book ids if you need test data for example
# will be expanded to help implement search later
@use_search_string
def fetch_with_title(title):
    """
    rough function to help with finding openlibrary ids during development
    will be refined later to help with adding search
    """
    fetch_url = "https://openlibrary.org/search.json?q="+title
    process_docs = lambda x: [strip_search_result_data(i) for i in x["docs"]]
    try:
        books_data = json_from_url(fetch_url, processing_func=process_docs)
    except Exception as e:
        books_data = None
    return books_data
