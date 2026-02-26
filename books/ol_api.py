import json
from urllib.request import urlopen
from urllib import HTTPError

# convenient work id for purposes of testing
# points to Hacker's Delight
test_workid = "OL8022414W"

# this will cache book data so that we dont need to fetch from internet every time
workid_cache = {}
author_cache = {}
cover_cache = {}

def fetch_with_workid(work_id):
    """
    Takes in an OpenLibrary ID (of format OL8022414W) and returns title, author(s), date and subjects of the book.
    """
    if work_id in workid_cache:
        return workid_cache[work_id]

    fetch_url = f"https://openlibrary.org/works/{work_id}.json"
    try:
        response = urlopen(fetch_url)
        book_data = json.load(response)
    except HTTPError as err:
        print(f"Couldn't fetch book {work_id}: {err}")
        return None # may change to raise
    except json.JSONDecodeError as err:
        print(f"Couldn't decode book {work_id}'s json: {err}")
        return None # may change to raise
    else:
        key_data = {
            "title": book_data.get("title", "Unknown"),
            "authors": fetch_authors(book_data.get("authors", None)),
            "date": book_data.get("first_publish_date"),
            "subjects": book_data.get("subjects", []),
        }
        workid_cache[work_id] = key_data
        return key_data

def cover_from_workid(work_id, is_thumbnail):
    """
    Takes in an OpenLibrary ID and returns the url to OpenLibrary's cover (which can then be used as your src in the img tag). Set is_thumbnail to true if the cover's display will be quite small (like in a list)
    """
    unknown_cover = "static/unknown"
    base = f"https://covers.openlibrary.org/b/olid/{work_id}"
    size = "M"
    if is_thumbnail: size = "S"

    if work_id in cover_cache: return f"{cover_cache[work_id]}-{size}.jpg"
    check_exists_url = f"{base}.json"
    try:
        response = urlopen(check_exists_url)
        cover_data = json.load(response)
    except HTTPError as err:
        if err.code != 404:
            print(f"Non 404 error encountered when fetching cover for {work_id}: {err}")
        cover_cache[work_id] = unknown_cover
        return f"{unknown_cover}-{size}.jpg"
    else:
        cover_cache[work_id] = base
        return f"{base}-{size}.jpg"
    return img


def fetch_authors(author_field):
    """
    Helper function for fetch_with_workid. Not recommended to use outside of that.
    """
    if author_field == None: return []
    author_names = []
    for item in author_field:
        author_id = item["author"]["key"]
        if author_id in author_cache:
            author = author_cache[author_id]
        else:
            fetch_url = f"https://openlibrary.org{author_id}.json"
            try:
                response = urlopen(fetch_url)
                author_data = json.load(response)
                author = author_data.get("name", "Unknown")
            except:
                print("Error occured when fetching authors")
                author = "Unknown"
            author_cache[author_id] = author
        author_names.append(author)

    return author_names

def validate_workid(work_id):
    """
    Checks if a given string is a valid OpenLibrary work ID.
    """
    if work_id[:2] != "OL":
        return False
    if work_id[-1] != "W":
        return False
    if not work_id[2:-1].isdigit():
        return False
    return True

# for now this is a helper function to help find book ids if you need test data for example
# will be expanded to help implement search later
def fetch_with_title(title):
    """
    rough function to help with finding openlibrary ids during development
    will be refined later to help with adding search
    """
    title = normalise_string(title)
    fetch_url = "https://openlibrary.org/search.json?q="+title
    response = urlopen(fetch_url)
    book_data = json.load(response)
    return book_data

def normalise_string(string):
    string = "".join([c for c in string.lower() if c.isalnum() or c == " "])
    string = "+".join(string.split(" "))
    return string
