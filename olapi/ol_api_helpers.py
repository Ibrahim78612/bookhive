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
    Converts a string like "Isn't_it_wonderful?" to "isnt+it+wonderful"
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
        use_args = [arg for arg in args]
        use_args[0] = string
        use_args = tuple(use_args)
        return func(*use_args, **kwargs)
    return wrapper

# ---
# GENERAL RETURN JSON FROM URL
# ---

@try_cache
def json_from_url(url, processing_func=lambda x: x):
    """
    Takes in a URL and tries to parse it as json. If successful, returns the dictionary formed by that json, otherwise errors.

    Can optionally take in a processing function, mainly used to trim down the amount of data in the cache. Whatever the processing function does IS ALSO PUT INTO THE CACHE so be careful with this functionality.
    """
    try:
        response = urlopen(url)
        json_data = json.load(response)
        json_data = processing_func(json_data)
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
            author = json_from_url(fetch_url, lambda x: x.get("name", "Unknown"))
        except:
            print("Error occured when fetching authors; suppressing")
            author = "Unknown"
        author_names.append(author)

    return author_names

# ---
# PROCESSING FUNCTIONS FOR JSON_FROM_URL
# ---

def get_from_dict(original, *args):
    new_dict = {}
    for key in args:
        new_dict[key] = original.get(key, None)
    return new_dict

def strip_book_data(book_data):
    key_data = get_from_dict(book_data, "title", "authors", "description", "first_publish_date", "subjects", "covers")
    if key_data["authors"] is not None:
        key_data["authors"] = fetch_authors(key_data["authors"])
    if key_data["covers"] is not None:
        key_data["covers"] = key_data["covers"][0]
    # filter out junk genres with numbers in them, common quirk of the open library
    if key_data["subjects"] is not None:
        subjects = key_data["subjects"]
        key_data["subjects"] = subject_filterer(subjects)
    return key_data

def strip_search_result_data(book_data):
    key_data = get_from_dict(book_data, "title", "author_name", "first_publish_year", "cover_i", "key")
    key_data["key"] = key_data["key"].split("/")[-1]
    # rename fields so it is more consistent with strip_book_data
    rename_field(key_data, "key", "workid")
    rename_field(key_data, "author_name", "authors")
    rename_field(key_data, "first_publish_year", "first_publish_date")
    key_data["cover"] = f"https://covers.openlibrary.org/b/id/{key_data['cover_i']}-S.jpg"
    return key_data

def subject_filterer(subjects):
    blacklisted_chars = [c for c in "1234567890,"]
    subjects = [subject for subject in subjects if not any(c in blacklisted_chars for c in subject)]
    return subjects

def rename_field(dictionary, old_name, new_name):
    dictionary[new_name] = dictionary[old_name]
    del old_name
