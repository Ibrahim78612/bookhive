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

def user_data_to_search(fetch_data):
    """
    Converts user model data to data useable by the search page.
    """
    pass
