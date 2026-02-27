import json
from urllib.request import urlopen
from urllib.error import HTTPError
from functools import wraps

url_cache = {}

# ---
# UTILITIES FOR VALIDATING STRINGS
# ---

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

def search_string(string):
    """
    Converts a string like "Isn't it wonderful?" to "isnt+it+wonderful"
    """
    string = "".join([c for c in string.lower() if c.isalnum() or c == " "])
    string = "+".join(string.split(" "))
    return string

# ---
# DECORATORS FOR CACHE/WORKID VALIDATION
# ---

def check_workid(func):
    """
    Checks if the first parameter of the given function is a valid OpenLibrary work id.
    """
    @wraps(func) # this part is to ensure metadata is not lost
    def wrapper(*args, **kwargs):
        work_id = args[0]
        if not validate_workid(work_id):
            raise ValueError(f"Invalid work_id: {work_id}")
        return func(*args, **kwargs)
    return wrapper

def try_cache(func):
    """
    Checks if the data is in the URL cache; if it is it returns the data, otherwise it executes the given function to retrieve the data (and if the function does not return an error, will add this to the URL cache).
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        key = args[0]
        if key in url_cache:
            return url_cache[key]
        try:
            result = func(*args, **kwargs)
        except:
            raise
        else:
            # if not an error, cache it
            url_cache[key] = result
            return result
    return wrapper

def use_search_string(func):
    """
    Converts the first parameter of the given function to a search string (see the description of search_string())
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        string = search_string(args[0])
        args[0] = string
        return func(*args, **kwargs)
    return wrapper

# ---
# GENERAL RETURN JSON FROM URL
# ---

@try_cache
def json_from_url(url):
    """
    Takes in a URL and tries to parse it as json. If successful, returns the dictionary formed by that json, otherwise errors.
    """
    try:
        response = urlopen(url)
        json_data = json.load(response)
        return json_data
    except Exception as e:
        raise

# ---
# FUNCTION USED INSIDE OF FETCH_FROM_WORKID
# ---

def fetch_authors(author_field):
    """
    Takes in an 'authors' json from OpenLibrary and converts that into a list of author names.
    Mainly used in fetch_work_id.
    """
    if author_field == None: return []
    author_names = []
    for item in author_field:
        author_id = item["author"]["key"]
        fetch_url = f"https://openlibrary.org{author_id}.json"
        try:
            author_data = json_from_url(fetch_url)
            author = author_data.get("name", "Unknown")
        except:
            print("Error occured when fetching authors; suppressing")
            author = "Unknown"
        author_names.append(author)

    return author_names
